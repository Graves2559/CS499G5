from dataclasses import dataclass


@dataclass(frozen=True)
class OCRResult:
    text: str
    model_id: str


@dataclass(frozen=True)
class SummaryResult:
    text: str
    model_id: str