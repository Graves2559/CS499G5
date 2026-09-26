"""
Entry point for the ClosedAI backend. Deliberately tiny: it just wires up
CORS (so a plain HTML file / dev frontend on a different origin can call it)
and mounts one router per feature.

As new work items come in (summarize, OCR upload, etc.), each one gets its
own file under routers/ with its own APIRouter -- add it here with one more
app.include_router(...) line. Nothing in this file should need to change
except that one line.

Run (from this backend/ folder):
    uvicorn main:app --reload --port 8000
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import define

app = FastAPI(title="ClosedAI Backend")

# Wide open for local dev across origins/ports. Tighten allow_origins to your
# real frontend's URL once you have one, instead of "*".
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(define.router, prefix="/api", tags=["define"])
# Next work item's router gets added the same way, e.g.:
# from routers import summarize
# app.include_router(summarize.router, prefix="/api", tags=["summarize"])


@app.get("/health")
def health():
    """Quick way to check the server is up: GET /health -> {"status": "ok"}"""
    return {"status": "ok"}
