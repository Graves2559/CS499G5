from typing import Sequence

from AI.domain.Models import ModelInfo


class StaticModelCatalog:
    """Curated choices that can be displayed as frontend buttons."""

    def __init__(self, models: Sequence[ModelInfo] | None = None):
        # Replace this with provider discovery or environment-based configuration
        # once the actual Ollama/OCR adapters are implemented.
        self._models = tuple(models or (
            ModelInfo("llama3.1:8b", "Llama 3.1 8B", "summarizer", True),
            ModelInfo("mistral:7b", "Mistral 7B", "summarizer", False),
        ))

    def list_models(self) -> Sequence[ModelInfo]:
        return self._models
