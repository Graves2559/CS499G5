from dataclasses import dataclass
from typing import Literal


ModelKind = Literal["summarizer", "ocr"]


@dataclass(frozen=True)
class ModelInfo:
    # Keep this provider-neutral. The frontend should use `id`; `name` is only display text.
    id: str
    name: str
    kind: ModelKind
    # This should eventually be determined by the provider adapter, not hard-coded here.
    available: bool
