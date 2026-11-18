from typing import Sequence

from AI.application.Ports import ModelCatalog
from AI.domain.Models import ModelInfo


class ModelCatalogService:
    def __init__(self, catalog: ModelCatalog):
        # Dependency injection keeps this service testable with a fake catalog.
        self.catalog = catalog

    def list_models(self) -> Sequence[ModelInfo]:
        # Add filtering/validation here if the UI should only receive usable models.
        return self.catalog.list_models()
