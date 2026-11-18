import os
from datetime import datetime, timezone
from uuid import uuid4

import ollama
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


router = APIRouter()

DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
MAX_SUMMARY_INPUT = 12000


class SummarizeRequest(BaseModel):
    text: str
    model: str | None = None


class SummaryRecord(BaseModel):
    id: str
    source_length: int
    summary: str
    model: str
    created_at: str


summaries: list[SummaryRecord] = []


@router.post("/summarize", response_model=SummaryRecord)
def summarize(payload: SummarizeRequest):
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text to sumarize must not be empty.")

    if len(text) > MAX_SUMMARY_INPUT:
        raise HTTPException(
            status_code=413,
            detail=f"Text to summarize must be {MAX_SUMMARY_INPUT} characters or fewer.",
        )

    model = payload.model or DEFAULT_MODEL
    prompt = (
        "This is my custom prompt"
        "Keep the important facts and do not invent information.\n\n"
        f"{text}"
    )

    try:
        response = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        result = response["message"]["content"].strip()
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                f"Summarization failed using Ollama model '{model}'. "
                "Make sure Ollama is running and the model is installed."
            ),
        ) from exc

    if not result:
        raise HTTPException(status_code=502, detail="The AI model returned an empty summary.")

    record = SummaryRecord(
        id=str(uuid4()),
        source_length=len(text),
        summary=result,
        model=model,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    summaries.append(record)
    return record


@router.get("/summaries", response_model=list[SummaryRecord])
def list_summaries():
    return summaries
