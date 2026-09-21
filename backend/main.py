"""
main.py
-------
FastAPI app for the Vestir Fashion AI Stylist backend.

Exposes:
  GET  /health   basic liveness + configuration check
  POST /chat     the main chat endpoint used by the frontend widget

Run with:
  uvicorn main:app --reload --port 8000
"""

import os
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

import model

load_dotenv()  # loads backend/.env into the environment

app = FastAPI(
    title="Vestir Fashion AI Stylist API",
    description="Backend API powering the Vestir AI fashion stylist chat widget.",
    version="1.0.0",
)

# Allow the frontend (served separately, e.g. via `python -m http.server`
# or a static host) to call this API during local development.
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if ALLOWED_ORIGINS == "*" else ALLOWED_ORIGINS.split(","),
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

MAX_MESSAGE_LENGTH = 1500
MAX_HISTORY_TURNS = 20


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., max_length=MAX_MESSAGE_LENGTH)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=MAX_MESSAGE_LENGTH)
    history: list[ChatTurn] = Field(default_factory=list)

    @field_validator("message")
    @classmethod
    def message_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("message must not be blank")
        return v.strip()

    @field_validator("history")
    @classmethod
    def cap_history(cls, v: list[ChatTurn]) -> list[ChatTurn]:
        return v[-MAX_HISTORY_TURNS:]


class ChatResponse(BaseModel):
    reply: str


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "provider_configured": model.is_configured(),
        "model": model.GROQ_MODEL,
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest):
    history = [{"role": t.role, "content": t.content} for t in payload.history]

    try:
        reply = await model.generate_reply(payload.message, history)
    except model.UpstreamError as exc:
        # Never leak raw provider errors/secrets to the browser —
        # UpstreamError messages are already safe, user-facing text.
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Something went wrong while styling your request. Please try again.",
        )

    return ChatResponse(reply=reply)
