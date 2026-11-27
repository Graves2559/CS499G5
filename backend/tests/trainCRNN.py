"""Train the CRNN on a small streaming subset of the MJSynth dataset."""

from __future__ import annotations

import argparse
import string
import sys
from collections.abc import Iterable, Iterator
from io import BytesIO
from pathlib import Path
from typing import Any
import torch
from datasets import Image as DatasetImage
from datasets import disable_progress_bars, load_dataset
from PIL import Image
from torch import Tensor, nn
from torch.optim import AdamW

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from AI.infrastructure.CRNN import CRNN


ALPHABET = string.ascii_letters + string.digits
BLANK_ID = 0
CHAR_TO_ID = {character: index + 1 for index, character in enumerate(ALPHABET)}
DATASET_NAME = "priyank-m/MJSynth_text_recognition"
IMAGE_HEIGHT = 32

disable_progress_bars()


def encode_label(label: str) -> list[int]:
    try:
        return [CHAR_TO_ID[character] for character in label]
    except KeyError as error:
        raise ValueError(f"Label contains unsupported character {error.args[0]!r}: {label!r}") from error


def prepare_image(image: Image.Image) -> tuple[Tensor, int]:
    image = image.convert("L")
    width = max(4, round(image.width * IMAGE_HEIGHT / image.height))
    image = image.resize((width, IMAGE_HEIGHT), Image.Resampling.BILINEAR)
    pixels = torch.frombuffer(bytearray(image.tobytes()), dtype=torch.uint8)
    tensor = pixels.reshape(IMAGE_HEIGHT, width).to(torch.float32).div_(255).unsqueeze(0)
    return tensor, width


def decode_dataset_image(value: Any) -> Image.Image:
    if isinstance(value, Image.Image):
        return value
    if not isinstance(value, dict):
        raise TypeError("Dataset image column did not produce image data.")

    image_bytes = value.get("bytes")
    image_path = value.get("path")
    source = BytesIO(image_bytes) if image_bytes is not None else image_path
    if source is None:
        raise ValueError("Dataset image has neither bytes nor a path.")

    with Image.open(source) as image:
        image.load()
        return image.copy()


def collate_batch(
    examples: list[tuple[Tensor, list[int], int]],
) -> tuple[Tensor, Tensor, Tensor, Tensor]:
    max_width = max(width for _, _, width in examples)
    images = torch.zeros((len(examples), 1, IMAGE_HEIGHT, max_width), dtype=torch.float32)

    encoded_labels: list[int] = []
    target_lengths = []
    image_widths = []
    for index, (image, label_ids, width) in enumerate(examples):
        images[index, :, :, :width] = image
        encoded_labels.extend(label_ids)
        target_lengths.append(len(label_ids))
        image_widths.append(width)

    return (
        images,
        torch.tensor(encoded_labels, dtype=torch.long),
        torch.tensor(target_lengths, dtype=torch.long),
        torch.tensor(image_widths, dtype=torch.long),
    )


def batches(
    dataset: Iterable[dict[str, Any]], batch_size: int, sample_limit: int
) -> Iterator[tuple[Tensor, Tensor, Tensor, Tensor]]:
    pending: list[tuple[Tensor, list[int], int]] = []
    iterator = iter(dataset)
    sample_count = 0
    try:
        for row_index, row in enumerate(iterator, start=1):
            try:
                image = decode_dataset_image(row["image"])
            except OSError as error:
                print(
                    f"Skipping unreadable image at streamed row {row_index}: {error}",
                    file=sys.stderr,
                )
                continue

            image_tensor, width = prepare_image(image)
            pending.append((image_tensor, encode_label(str(row["label"])), width))
            sample_count += 1

            if len(pending) == batch_size:
                yield collate_batch(pending)
                pending = []
            if sample_limit > 0 and sample_count >= sample_limit:
                break
    finally:
        close = getattr(iterator, "close", None)
        if close is not None:
            close()

    if pending:
        yield collate_batch(pending)


def cnn_output_lengths(input_widths: Tensor) -> Tensor:
    # The CRNN CNN downsamples width twice by a factor of two.
    return input_widths.div(4, rounding_mode="floor").clamp_min(1)


def ctc_greedy_decode(logits: Tensor, input_lengths: Tensor) -> list[str]:
    predictions = logits.argmax(dim=2).transpose(0, 1).cpu()
    decoded: list[str] = []
    for prediction, input_length in zip(predictions, input_lengths):
        previous_id = BLANK_ID
        characters: list[str] = []
        for token_id in prediction[:input_length].tolist():
            if token_id != BLANK_ID and token_id != previous_id:
                characters.append(ALPHABET[token_id - 1])
            previous_id = token_id
        decoded.append("".join(characters))
    return decoded


def save_loss_plot(
    train_losses: list[float],
    validation_epochs: list[int],
    validation_losses: list[float],
    output_path: Path,
) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure()
    plt.plot(range(1, len(train_losses) + 1), train_losses, label="Training")
    if validation_losses:
        plt.plot(
            validation_epochs,
            validation_losses,
            marker="o",
            label="Validation",
        )
    plt.xlabel("Epoch")
    plt.ylabel("CTC loss")
    plt.title("CRNN training and validation loss")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    temporary_path = output_path.with_name(
        f".{output_path.stem}.tmp{output_path.suffix}"
    )
    try:
        plt.savefig(temporary_path, dpi=150)
        temporary_path.replace(output_path)
    finally:
        plt.close()
        temporary_path.unlink(missing_ok=True)


def train(args: argparse.Namespace) -> None:
    torch.manual_seed(args.seed)
    alphabet_size = len(ALPHABET) + 1  # CTC blank is class 0.
    best_val_loss = float("inf")
    train_losses: list[float] = []
    validation_epochs: list[int] = []
    validation_losses: list[float] = []

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = CRNN(num_classes=alphabet_size, hidden_size=args.hidden_size).to(device)
    optimizer = AdamW(model.parameters(), lr=args.learning_rate)
    ctc_loss = nn.CTCLoss(blank=BLANK_ID, zero_infinity=True)
    args.checkpoint.parent.mkdir(parents=True, exist_ok=True)

    for epoch in range(args.epochs):
        model.train()
        train_dataset = load_dataset(
            DATASET_NAME, split="train", streaming=True
        ).cast_column("image", DatasetImage(decode=False))
        if args.shuffle_buffer > 1:
            train_dataset = train_dataset.shuffle(
                seed=args.seed + epoch,
                buffer_size=args.shuffle_buffer,
            )

        epoch_loss = 0.0
        batch_count = 0

        for images, targets, target_lengths, image_widths in batches(
            train_dataset, args.batch_size, args.samples
        ):
            images = images.to(device)
            logits = model(images)
            log_probs = logits.log_softmax(dim=2)
            input_lengths = cnn_output_lengths(image_widths)
            loss = ctc_loss(log_probs, targets, input_lengths, target_lengths)

            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()
            batch_count += 1

        if batch_count == 0:
            raise RuntimeError("The dataset produced no training batches.")

        train_loss = epoch_loss / batch_count
        train_losses.append(train_loss)
        if epoch > 0 and epoch % args.validation_frequency != 0:
            print(
                f"Epoch {epoch + 1}/{args.epochs} | "
                f"train_loss={train_loss:.4f} | validation_skipped"
            )
            save_loss_plot(
                train_losses,
                validation_epochs,
                validation_losses,
                args.loss_plot,
            )
            continue

        model.eval()
        val_dataset = load_dataset(
            DATASET_NAME, split="val", streaming=True
        ).cast_column("image", DatasetImage(decode=False))
        val_loss_total = 0.0
        val_batch_count = 0
        correct_predictions = 0
        validation_samples = 0
        with torch.no_grad():
            for images, targets, target_lengths, image_widths in batches(
                val_dataset, args.batch_size, args.val_samples
            ):
                images = images.to(device)
                logits = model(images)
                log_probs = logits.log_softmax(dim=2)
                input_lengths = cnn_output_lengths(image_widths)
                val_loss_total += ctc_loss(
                    log_probs, targets, input_lengths, target_lengths
                ).item()
                val_batch_count += 1

                predictions = ctc_greedy_decode(logits, input_lengths)
                target_sequences = targets.split(target_lengths.tolist())
                for pred_text, target_seq in zip(predictions, target_sequences):
                    target_text = "".join(ALPHABET[i - 1] for i in target_seq)
                    if pred_text == target_text:
                        correct_predictions += 1
                validation_samples += len(target_sequences)

        if val_batch_count == 0:
            raise RuntimeError("The validation split produced no batches.")
        validation_loss = val_loss_total / val_batch_count
        validation_epochs.append(epoch + 1)
        validation_losses.append(validation_loss)
        validation_accuracy = correct_predictions / validation_samples
        print(
            f"Epoch {epoch + 1}/{args.epochs} | "
            f"train_loss={train_loss:.4f} | "
            f"val_loss={validation_loss:.4f} | "
            f"val_word_accuracy={validation_accuracy:.4f}"
        )
        if validation_loss < best_val_loss:
            best_val_loss = validation_loss
            torch.save(
                {
                    "epoch": epoch + 1,
                    "model_state_dict": model.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                    "alphabet": ALPHABET,
                    "blank_id": BLANK_ID,
                    "image_height": IMAGE_HEIGHT,
                    "hidden_size": args.hidden_size,
                    "validation_loss": validation_loss,
                },
                args.checkpoint,
            )
            print(f"Saved best checkpoint to {args.checkpoint}")

        save_loss_plot(
            train_losses,
            validation_epochs,
            validation_losses,
            args.loss_plot,
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=32, help="Rows to stream per epoch; 0 means all.")
    parser.add_argument(
        "--val-samples",
        type=int,
        default=256,
        help="Validation rows per epoch; 0 means the whole validation split.",
    )
    parser.add_argument(
        "--shuffle-buffer",
        type=int,
        default=10000,
        help="Rows held for approximate streaming shuffle; larger values use more memory.",
    )
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--hidden-size", type=int, default=128)
    parser.add_argument("--learning-rate", type=float, default=1e-3)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument(
        "--validation-frequency",
        type=int,
        default=1,
        help="Validate on the first epoch and then every N epochs.",
    )
    parser.add_argument(
        "--checkpoint",
        type=Path,
        default=Path("crnn_checkpoint.pt"),
        help="Where to save the trained model.",
    )
    parser.add_argument(
        "--loss-plot",
        type=Path,
        default=Path("crnn_loss.png"),
        help="Where to save the training/validation loss graph.",
    )
    args = parser.parse_args()
    if args.samples < 0 or args.val_samples < 0:
        parser.error("--samples and --val-samples must be 0 (all rows) or positive integers.")
    if args.batch_size < 1 or args.epochs < 1 or args.hidden_size < 1:
        parser.error("--batch-size, --epochs, and --hidden-size must be positive.")
    if args.validation_frequency < 1:
        parser.error("--validation-frequency must be positive.")
    if args.shuffle_buffer < 1:
        parser.error("--shuffle-buffer must be positive.")
    return args


if __name__ == "__main__":
    train(parse_args())