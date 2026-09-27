from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from llm import run_prompt, DEFAULT_MODEL

router = APIRouter()

DEFINE_PROMPT_TEMPLATE = (
    "Define the following term or phrase clearly and concisely, in 1-2 "
    "sentences. If it could mean more than one thing, give the most common "
    "meaning and briefly note that it can vary by context.\n\n{text}"
)


class DefineRequest(BaseModel):
    text: str
    model: str | None = None


class DefineResponse(BaseModel):
    definition: str
    model: str


@router.post("/define", response_model=DefineResponse)
def define(payload: DefineRequest):
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text must not be empty")

    model = payload.model or DEFAULT_MODEL
    try:
        definition = run_prompt(
            DEFINE_PROMPT_TEMPLATE.format(text=text),
            model=model,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to generate definition: {exc}",
        ) from exc

    return DefineResponse(definition=definition, model=model)
