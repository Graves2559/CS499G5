"""CRNN model skeleton for recognizing a single cropped text line.

Tensor shapes through the model:
    input images: [B, 1, H, W]
    CNN features: [B, F, 1, T]
    sequence:     [T, B, F]
    logits:       [T, B, C]  (C includes the CTC blank class)
"""
from torch import Tensor, nn


class CRNN(nn.Module):
    def __init__(self, num_classes: int, hidden_size: int = 256) -> None:
        super().__init__()
        cnn_out_channels = 256
        # Define a CNN that extracts features from the input image.
        self.cnn = nn.Sequential(
            nn.Conv2d(1, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),          # H/2, W/2

            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),          # H/4, W/4

            nn.Conv2d(128, cnn_out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(cnn_out_channels),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=(2, 1), stride=(2, 1)),  # H/8, W/4

            nn.Conv2d(cnn_out_channels, cnn_out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(cnn_out_channels),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d((1, None)),                # [B, 256, 1, T]
            )
        #BiDirectional LSTM for sequence modeling across the width of the image.
        self.rnn = nn.LSTM(
            input_size=cnn_out_channels,
            hidden_size=hidden_size,
            num_layers=2,
            bidirectional=True,
            batch_first=False,  # LSTM expects [T, B, F]
        )
        #Map the LSTM outputs to logits for each character class (including the CTC blank).
        self.classifier = nn.Linear(hidden_size * 2, num_classes)  # Bidirectional

    def forward(self, images: Tensor) -> Tensor:
        features = self.cnn(images)                 # [B, F, 1, T]
        sequence = features.squeeze(2).permute(2, 0, 1)  # [T, B, F]
        sequence, _ = self.rnn(sequence)            # [T, B, 2 * hidden_size]
        logits = self.classifier(sequence)           # [T, B, C]
        return logits
