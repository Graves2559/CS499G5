from pydantic import BaseModel


class ModelResponse(BaseModel):
    # This is the public contract consumed by frontend model-selection buttons.
    id: str
    name: str
    kind: str
    available: bool