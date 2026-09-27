from pickle import GET

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import define

app = FastAPI(title="ClosedAI Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(define.router, prefix="/api")

@app.get("/health")
def health_check():
    return {"status": "ok"}
