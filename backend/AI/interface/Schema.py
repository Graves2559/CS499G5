from pydantic import BaseModel


class ModelResponse(BaseModel):
    # This is the public contract consumed by frontend model-selection buttons.
    id: str
    name: str
    kind: str
    available: bool


class AIResultResponse(BaseModel):
    entry_id: str
    name: str
    data: str
    operation: str
    ocr_model_id: str | None = None
    llm_model_id: str | None = None