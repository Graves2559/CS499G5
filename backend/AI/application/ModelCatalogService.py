from typing import Sequence

from AI.application.Ports import ModelCatalog
from AI.domain.Models import ModelInfo
from CommonErrors.Errors import ValidationError


class ModelCatalogService:
    def __init__(self, catalog: ModelCatalog):
        # Dependency injection keeps this service testable with a fake catalog.
        self.catalog = catalog

    def list_models(self) -> Sequence[ModelInfo]:
        # Add filtering/validation here if the UI should only receive usable models.
        return self.catalog.list_models()

    def require_model(self, model_id: str, kind: str) -> ModelInfo:
        for model in self.catalog.list_models():
            if model.id == model_id and model.kind == kind and model.available:
                return model
        raise ValidationError(f"Unknown or unavailable {kind} model: {model_id}")
