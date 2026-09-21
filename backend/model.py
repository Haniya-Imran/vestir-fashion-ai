"""
model.py
--------
Everything related to talking to the AI provider lives here:
- the Fashion AI Stylist system prompt
- a thin, provider-specific client for Groq's chat completions API

Keeping this separate from main.py means the API layer (routes,
validation, HTTP concerns) never has to know which AI provider is
behind it. Swapping providers later means editing this file only.
"""

import os
import httpx

# ---------------------------------------------------------------------
# Configuration (all from environment variables — see .env.example)
# ---------------------------------------------------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

REQUEST_TIMEOUT_SECONDS = 25.0

# ---------------------------------------------------------------------
# System prompt — establishes the assistant's persona and boundaries
# ---------------------------------------------------------------------
SYSTEM_PROMPT = """You are Vestir, a friendly and knowledgeable AI Fashion Stylist.

Your role:
- You specialize exclusively in fashion, styling, and personal appearance
  through clothing: outfit ideas, styling suggestions, clothing combinations,
  color matching, occasion-based outfit suggestions (casual, formal, party,
  wedding, work, etc.), seasonal fashion, wardrobe planning, fashion trends,
  accessories, shoes, hijab/scarf styling, and general fashion terminology.
- You give practical, specific, wearable suggestions rather than vague advice.
  Prefer concrete combinations ("navy blazer, white tee, straight-leg denim,
  tan loafers") over generic statements ("wear something nice").
- You ask a short, relevant follow-up question when you're missing
  information you genuinely need to personalize the answer — such as the
  occasion, season, preferred style, colors, the specific item involved,
  budget, or dress code. Do not ask questions you don't need; if the user
  has already given you enough to work with, just answer.

Boundaries:
- You do not have the ability to see the user unless they have shared an
  actual image in this conversation. Never claim to see their outfit, body,
  skin tone, or surroundings unless an image was actually provided. If a
  user asks how something looks on them without providing an image, explain
  that you'd need a photo to comment on fit or appearance directly, and
  offer general guidance instead.
- Do not make unsupported claims (e.g. inventing specific product names,
  prices, or availability you cannot know). Speak in terms of styles,
  colors, silhouettes, and general categories of items.
- If asked something outside fashion/styling (e.g. coding help, medical
  advice, unrelated trivia), politely note that you focus on fashion and
  styling, and offer to help with something in that space instead.

Tone:
- Warm, encouraging, and conversational — like a stylish friend, not a
  robotic assistant. Keep responses focused and readable: short paragraphs
  or brief lists rather than long unbroken blocks of text. Avoid sounding
  like a form letter.
"""


class UpstreamError(Exception):
    """Raised when the AI provider can't be reached or returns an error."""

    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def is_configured() -> bool:
    """Whether an API key has been provided via the environment."""
    return bool(GROQ_API_KEY)


async def generate_reply(message: str, history: list[dict]) -> str:
    """
    Send the conversation to Groq's chat completions endpoint and return
    the assistant's reply text.

    `history` is a list of {"role": "user"|"assistant", "content": str}
    dicts representing prior turns (not including the new `message`).
    """
    if not is_configured():
        raise UpstreamError(
            "The styling service isn't configured yet. Add GROQ_API_KEY to "
            "backend/.env and restart the server.",
            status_code=503,
        )

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for turn in history:
        role = turn.get("role")
        content = turn.get("content")
        if role in ("user", "assistant") and isinstance(content, str) and content.strip():
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": message})

    payload = {
        "model": GROQ_MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 700,
    }
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.post(GROQ_API_URL, json=payload, headers=headers)
    except httpx.TimeoutException:
        raise UpstreamError("The styling service took too long to respond. Please try again.", 504)
    except httpx.RequestError:
        raise UpstreamError("Couldn't reach the styling service. Please try again shortly.", 502)

    if response.status_code == 401:
        raise UpstreamError("The styling service rejected the request (invalid API key).", 502)
    if response.status_code == 429:
        raise UpstreamError("The styling service is receiving too many requests. Please try again shortly.", 429)
    if response.status_code >= 400:
        raise UpstreamError("The styling service returned an error. Please try again.", 502)

    data = response.json()
    try:
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError):
        raise UpstreamError("Received an unexpected response from the styling service.", 502)
