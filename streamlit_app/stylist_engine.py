"""
stylist_engine.py
------------------
Shared "brain" for the Vestir Streamlit app: the Fashion AI Stylist
system prompt plus a small synchronous Groq client.

This mirrors backend/model.py (used by the FastAPI version) but uses
`requests` instead of `httpx` since Streamlit apps run synchronously.
Keeping the prompt and API logic in their own module — separate from
app.py's UI code — keeps things easy to read and to swap providers later.
"""

import requests
import streamlit as st

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
REQUEST_TIMEOUT_SECONDS = 25

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


def _get_config():
    """
    Read GROQ_API_KEY / GROQ_MODEL from Streamlit secrets.
    On Streamlit Community Cloud, set these in
    App settings -> Secrets (not committed to the repo).
    """
    api_key = st.secrets.get("GROQ_API_KEY", "")
    model = st.secrets.get("GROQ_MODEL", "llama-3.3-70b-versatile")
    return api_key, model


def is_configured() -> bool:
    api_key, _ = _get_config()
    return bool(api_key)


def generate_reply(message: str, history: list[dict]) -> str:
    """
    history: list of {"role": "user"|"assistant", "content": str}
    Returns the assistant's reply text, or raises UpstreamError.
    """
    api_key, model = _get_config()
    if not api_key:
        raise UpstreamError(
            "The styling service isn't configured yet. Add GROQ_API_KEY in "
            "this app's Settings -> Secrets, then reboot the app."
        )

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for turn in history:
        role = turn.get("role")
        content = turn.get("content")
        if role in ("user", "assistant") and isinstance(content, str) and content.strip():
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": message})

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 700,
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    try:
        response = requests.post(
            GROQ_API_URL, json=payload, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS
        )
    except requests.Timeout:
        raise UpstreamError("The styling service took too long to respond. Please try again.")
    except requests.RequestException:
        raise UpstreamError("Couldn't reach the styling service. Please try again shortly.")

    if response.status_code == 401:
        raise UpstreamError("The styling service rejected the request (invalid API key).")
    if response.status_code == 429:
        raise UpstreamError("The styling service is receiving too many requests. Please try again shortly.")
    if response.status_code >= 400:
        raise UpstreamError("The styling service returned an error. Please try again.")

    data = response.json()
    try:
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError):
        raise UpstreamError("Received an unexpected response from the styling service.")
