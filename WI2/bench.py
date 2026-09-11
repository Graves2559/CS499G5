import argparse
import csv
import os
import subprocess
import time
from pathlib import Path

import psutil

ROOT = Path(__file__).parent


def gpu_usage():
    """Read GPU utilization % and dedicated memory (MB) via Windows performance
    counters instead of nvidia-smi, so this works on AMD/Intel GPUs too, not
    just NVIDIA. Returns ("unavailable", "unavailable") if the counters can't
    be read."""
    # NOTE: earlier version joined the two values with a comma, e.g. "12.3,450.6".
    # On any Windows locale that uses a comma as the decimal separator (common
    # outside en-US), $u.Sum.ToString() itself contains a comma, so the split(",")
    # below silently produced garbage or a caught exception -> "unavailable" for
    # every single row. Fixed by (a) forcing invariant-culture (period decimal)
    # formatting and (b) using "|" as the field separator so it can never collide
    # with a decimal mark regardless of locale.
    ps_cmd = (
        "$ErrorActionPreference='SilentlyContinue';"
        "$ic=[System.Globalization.CultureInfo]::InvariantCulture;"
        "$u=(Get-Counter '\\GPU Engine(*)\\Utilization Percentage').CounterSamples "
        "| Measure-Object -Property CookedValue -Sum;"
        "$m=(Get-Counter '\\GPU Process Memory(*)\\Dedicated Usage').CounterSamples "
        "| Measure-Object -Property CookedValue -Sum;"
        "Write-Output ($u.Sum.ToString('F1',$ic) + '|' + ($m.Sum/1MB).ToString('F1',$ic))"
    )
    try:
        output = subprocess.check_output(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=10,
        ).strip()
        utilization, memory = [v.strip() for v in output.split("|")]
        if not utilization or not memory:
            raise ValueError("empty counter output")
        return utilization, memory
    except Exception:
        return "unavailable", "unavailable"


def run_logged(name, operation, image_path, writer):
    process = psutil.Process(os.getpid())
    process.cpu_percent(None)
    start = time.perf_counter()
    result = operation(image_path)
    elapsed = time.perf_counter() - start
    gpu_percent, gpu_memory = gpu_usage()
    row = {
        "test": name,
        "image": str(image_path),
        "seconds": f"{elapsed:.3f}",
        "cpu_percent": f"{process.cpu_percent():.1f}",
        "ram_mb": f"{process.memory_info().rss / 1024 / 1024:.1f}",
        "gpu_percent": gpu_percent,
        "gpu_memory_mb": gpu_memory,
        "result": result.replace("\n", " ")[:300],
    }
    writer.writerow(row)
    return row


def iter_images(images_dir, limit):
    exts = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}
    images = sorted(p for p in Path(images_dir).rglob("*") if p.suffix.lower() in exts)
    if not images:
        raise SystemExit(f"No images found under {images_dir}")
    return images[:limit]


def _bench(name, operation, images_dir, limit, log_path):
    images = iter_images(images_dir, limit)
    fields = ["test", "image", "seconds", "cpu_percent", "ram_mb", "gpu_percent", "gpu_memory_mb", "result"]
    rows = []
    write_header = not log_path.exists()
    with log_path.open("a", newline="", encoding="utf-8") as log_file:
        writer = csv.DictWriter(log_file, fieldnames=fields)
        if write_header:
            writer.writeheader()
        skipped = 0
        for i, image_path in enumerate(images, 1):
            try:
                row = run_logged(name, operation, image_path, writer)
            except Exception as exc:
                skipped += 1
                print(f"[{i}/{len(images)}] {name}: SKIPPED ({image_path}) -- {exc}")
                continue
            rows.append(row)
            print(f"[{i}/{len(images)}] {name}: {row['seconds']}s "
                  f"cpu={row['cpu_percent']}% ram={row['ram_mb']}MB gpu={row['gpu_percent']}%")

    if skipped:
        print(f"\n{skipped} image(s) skipped due to errors (e.g. unreadable files) -- "
              f"excluded from the averages below.")
    if not rows:
        print("No images processed successfully -- nothing to average.")
        return

    avg_seconds = sum(float(r["seconds"]) for r in rows) / len(rows)
    cpu_vals = [float(r["cpu_percent"]) for r in rows]
    ram_vals = [float(r["ram_mb"]) for r in rows]
    gpu_vals = [float(r["gpu_percent"]) for r in rows if r["gpu_percent"] != "unavailable"]
    gpu_mem_vals = [float(r["gpu_memory_mb"]) for r in rows if r["gpu_memory_mb"] != "unavailable"]

    print(f"\n=== {name} averages over {len(rows)} images ===")
    print(f"time:    {avg_seconds:.3f} s")
    print(f"cpu:     {sum(cpu_vals)/len(cpu_vals):.1f} %")
    print(f"ram:     {sum(ram_vals)/len(ram_vals):.1f} MB")
    if gpu_vals:
        print(f"gpu:     {sum(gpu_vals)/len(gpu_vals):.1f} %")
        print(f"gpu_mem: {sum(gpu_mem_vals)/len(gpu_mem_vals):.1f} MB")
    else:
        print("gpu:     unavailable (perf counters not readable on this system)")


def run_trocr(images_dir, limit, model_dir, log_path):
    import torch
    from PIL import Image
    from transformers import TrOCRProcessor, VisionEncoderDecoderModel

    if not model_dir.exists():
        raise SystemExit(
            f"TrOCR model not found at {model_dir}.\n"
            f"Download it first, e.g.:\n"
            f'  .venv-paddle\\Scripts\\python.exe -c "from huggingface_hub import snapshot_download; '
            f"snapshot_download('microsoft/trocr-base-handwritten', local_dir='{model_dir}')\""
        )

    device = "cuda" if torch.cuda.is_available() else "cpu"
    processor = TrOCRProcessor.from_pretrained(model_dir)
    model = VisionEncoderDecoderModel.from_pretrained(model_dir).to(device)

    def operation(image_path):
        image = Image.open(image_path).convert("RGB")
        pixel_values = processor(images=image, return_tensors="pt").pixel_values.to(device)
        generated_ids = model.generate(pixel_values)
        return processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

    _bench("trocr", operation, images_dir, limit, log_path)


def _rapidocr_result_to_text(result):
    """RapidOCR's result object shape has shifted across versions, so try the
    known attribute first and fall back to a raw string rather than silently
    producing empty output that would look like a false 'it works' signal."""
    txts = getattr(result, "txts", None)
    if txts:
        return " ".join(str(t) for t in txts)
    if isinstance(result, (list, tuple)):
        texts = []
        for item in result:
            try:
                texts.append(str(item[1]))
            except (IndexError, TypeError):
                texts.append(str(item))
        return " ".join(texts)
    return str(result)


def run_rapidocr(images_dir, limit, log_path, use_dml):
    import onnxruntime as ort
    from rapidocr import ModelType, OCRVersion, RapidOCR

    # Definitive GPU check, independent of the Windows perf-counter monitoring
    # above (which can fail to read for unrelated reasons): onnxruntime always
    # knows which execution providers are actually installed/available. If
    # "DmlExecutionProvider" isn't in this list, onnxruntime-directml isn't
    # correctly installed and nothing below will run on GPU no matter what
    # use_dml is set to.
    available = ort.get_available_providers()
    print(f"onnxruntime available providers: {available}")
    if use_dml and "DmlExecutionProvider" not in available:
        print("WARNING: DmlExecutionProvider not available -- falling back to CPU. "
              "Re-check `pip install onnxruntime-directml` in this venv.")

    # NOTE: "ocr_version"/"model_type" don't live under Global -- each of Det/Cls/Rec
    # has its own copy (confirmed from config.yaml in the installed package). Also
    # forcing model_type=SERVER here to match the PP-OCRv5_server_det/rec models the
    # PaddleOCR benchmark used -- RapidOCR defaults to the lighter "small" variant,
    # which would otherwise make this comparison apples-to-oranges (faster partly
    # because it's a smaller model, not just because of the engine/GPU difference).
    params = {
        "Det.ocr_version": OCRVersion.PPOCRV5,
        "Det.model_type": ModelType.SERVER,
        "Rec.ocr_version": OCRVersion.PPOCRV5,
        "Rec.model_type": ModelType.SERVER,
    }
    if use_dml:
        params["EngineConfig.onnxruntime.use_dml"] = True
    engine = RapidOCR(params=params)

    def operation(image_path):
        return _rapidocr_result_to_text(engine(str(image_path)))

    _bench("rapidocr_v5", operation, images_dir, limit, log_path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", required=True, choices=["trocr", "rapidocr"])
    parser.add_argument("--images-dir", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--model-dir", type=Path, default=ROOT / "models" / "trocr-base-handwritten")
    # No shared default filename here on purpose: a shared default across engines
    # is what caused ocr_benchmark.csv to mix rows from different runs/engines
    # together. Each engine now gets its own default file under results/, so
    # forgetting --log can't mix data anymore.
    parser.add_argument("--log", type=Path, default=None)
    parser.add_argument("--no-dml", action="store_true", help="Disable DirectML, force onnxruntime CPU provider")
    args = parser.parse_args()

    log_path = args.log or (ROOT / "results" / f"ocr_benchmark_{args.engine}.csv")
    log_path.parent.mkdir(parents=True, exist_ok=True)

    if args.engine == "trocr":
        run_trocr(args.images_dir, args.limit, args.model_dir, log_path)
    else:
        run_rapidocr(args.images_dir, args.limit, log_path, use_dml=not args.no_dml)


if __name__ == "__main__":
    main()
