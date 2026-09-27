"""
The "AI defines it" work item: accepts some highlighted text and returns a
short definition. This is the template for future feature routers -- once
this one works end to end, copy its shape for summarize.py etc.

Goal for this file:
    - A request model: {"text": "...", "model": optional override}
    - A response model: {"definition": "...", "model": "..."}
    - A POST /define route that:
        1. Strips the incoming text; rejects it with a 400 if it's empty
        2. Falls back to DEFAULT_MODEL if no model override was given
        3. Builds a prompt from DEFINE_PROMPT_TEMPLATE + the text
        4. Calls llm.run_prompt(...) inside a try/except
        5. Returns the definition, or a 502 if the call to Ollama itself
           failed (not running, model not pulled, etc.)
"""

# TODO: from fastapi import APIRouter, HTTPException
# TODO: from pydantic import BaseModel
# TODO: from llm import run_prompt, DEFAULT_MODEL

# TODO: router = APIRouter()

DEFINE_PROMPT_TEMPLATE = (
    "Define the following term or phrase clearly and concisely, in 1-2 "
    "sentences. If it could mean more than one thing, give the most common "
    "meaning and briefly note that it can vary by context.\n\n{text}"
)


# TODO: class DefineRequest(BaseModel):
#     text: str
#     model: str | None = None


# TODO: class DefineResponse(BaseModel):
#     definition: str
#     model: str


# TODO: @router.post("/define", response_model=DefineResponse)
# def define(payload: DefineRequest):
#     - text = payload.text.strip(); raise HTTPException(400, ...) if empty
#     - model = payload.model or DEFAULT_MODEL
#     - try: definition = run_prompt(DEFINE_PROMPT_TEMPLATE.format(text=text), model=model)
#       except Exception as exc: raise HTTPException(502, detail=f"...: {exc}")
#     - return DefineResponse(definition=definition, model=model)
