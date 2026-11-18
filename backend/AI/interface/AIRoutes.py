from fastapi import APIRouter

from AI.application.ModelCatalogService import ModelCatalogService
from AI.domain.Models import ModelInfo
from AI.interface.Schema import ModelResponse


def _to_response(model: ModelInfo) -> ModelResponse:
    return ModelResponse(
        id=model.id,
        name=model.name,
        kind=model.kind,
        available=model.available,
    )


def buildAIRouter(catalog: ModelCatalogService) -> APIRouter:
    # Keep route functions thin: validate HTTP input, call an application service,
    # and translate domain results into response schemas.
    router = APIRouter(prefix="/api/ai", tags=["AI"])

    @router.get("/models", response_model=list[ModelResponse])
    def listModels() -> list[ModelResponse]:
        return [_to_response(model) for model in catalog.list_models()]

    return router