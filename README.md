# Vestir — AI Fashion Stylist

A premium, pink fashion-tech landing page with an integrated floating AI chat
assistant that gives personalized styling advice: outfit ideas, color
matching, occasion dressing, wardrobe help, accessories, and more.

## Features

- Elegant, editorial landing page (hero, AI showcase, features, how-it-works,
  use cases, testimonial, final CTA, footer) in a blush/rose/cream/charcoal
  design system — no stock photos, no generic chatbot imagery.
- Floating AI Stylist chat widget (bottom-right) that opens a compact panel
  over the page, with a branded launcher button, welcome state, fashion-only
  quick actions, typing indicator, copy/regenerate, retry-on-error, and
  "new chat".
- FastAPI backend that keeps the AI provider's API key server-side only,
  with a dedicated Fashion AI Stylist system prompt, input validation, and
  clean error handling.
- Fully responsive, keyboard-accessible, with visible focus states.

## Tech stack

- **Frontend:** plain HTML, CSS, and JavaScript (no build step required)
- **Backend:** Python, FastAPI, httpx
- **AI provider:** Groq chat completions API (model configurable via `.env`)

## Project structure

```
fashion-ai-stylist/
├── frontend/
│   ├── index.html      # landing page + chat widget markup
│   ├── style.css        # design system + component styles
│   ├── script.js        # nav + chat widget behavior, calls the backend
│   └── assets/
│       └── favicon.svg  # Vestir brand mark
│
├── backend/                      # FastAPI version (local dev/testing)
│   ├── main.py                    # FastAPI app, POST /chat, GET /health
│   ├── model.py                    # system prompt + Groq API client
│   ├── requirements.txt
│   ├── .env.example                # copy to .env and add your key
│   └── .env                        # (you create this — never committed)
│
├── streamlit_app/                # Streamlit version (deploy target)
│   ├── app.py                      # the chatbot UI itself
│   ├── stylist_engine.py            # same system prompt + Groq client, sync
│   ├── requirements.txt
│   └── .streamlit/
│       ├── config.toml              # theme to match the pink design system
│       └── secrets.toml.example     # copy to secrets.toml locally; use
│                                     # Streamlit Cloud's Secrets UI in prod
│
├── .gitignore
└── README.md
```

## Setup

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Open `backend/.env` and paste your Groq API key:

```
GROQ_API_KEY=your_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

Get a key from https://console.groq.com/keys. **This file is never sent to
the browser or committed to git** — `.gitignore` already excludes it.

Run the backend:

```bash
uvicorn main:app --reload --port 8000
```

Check it's alive: open http://127.0.0.1:8000/health — you should see
`"provider_configured": true` once your key is in place.

### 2. Frontend

The frontend is static, so any local server works:

```bash
cd frontend
python -m http.server 5500
```

Then open http://127.0.0.1:5500 in your browser.

By default the widget calls the backend at `http://127.0.0.1:8000`. If you
serve the backend elsewhere, set this before `script.js` loads in
`index.html`:

```html
<script>window.VESTIR_API_BASE = "https://your-backend-url";</script>
<script src="script.js"></script>
```

## Testing the chatbot

1. With both servers running, open the frontend URL.
2. Click **Try AI Stylist** (navbar, hero, or final CTA) or the floating
   button in the bottom-right corner.
3. Try a quick action (e.g. "Style an Outfit") or type your own message and
   press **Enter** to send (Shift+Enter for a new line).
4. You should see a typing indicator, then a reply from Vestir.
5. To test error handling, stop the backend and send a message — you'll see
   a friendly error with a **Try again** button.
6. Resize the browser or use device emulation to confirm the chat panel and
   landing page stay usable on mobile.

## Deployment (Vercel + Streamlit Cloud)

The teacher's brief asks for the frontend on **Vercel** and the backend on
**Streamlit**. Since Streamlit apps serve their own UI rather than exposing
a JSON API, the chatbot itself becomes a Streamlit app (`streamlit_app/`),
and the Vercel-hosted landing page embeds it in an iframe inside the
floating chat panel. The FastAPI backend (`backend/`) still works for local
development/testing, but isn't part of this deployment path.

### 1. Deploy the chatbot on Streamlit Community Cloud

1. Push this repo to GitHub (`.env`/`secrets.toml` are git-ignored, so your
   key won't be committed).
2. Go to https://share.streamlit.io, "New app", point it at your repo with:
   - **Main file path:** `streamlit_app/app.py`
3. In the app's **Settings → Secrets**, add:
   ```
   GROQ_API_KEY = "your_api_key_here"
   GROQ_MODEL = "llama-3.3-70b-versatile"
   ```
4. Deploy. Note the app's URL, e.g. `https://your-app.streamlit.app`.

### 2. Deploy the landing page on Vercel

1. In Vercel, "New Project" → import this repo.
2. Set **Root Directory** to `frontend`. Framework preset: **Other** (it's
   static HTML/CSS/JS — no build step).
3. Before deploying, open `frontend/index.html` and set:
   ```html
   <script>window.VESTIR_STREAMLIT_URL = "https://your-app.streamlit.app";</script>
   ```
   with the URL from step 1. Commit and push.
4. Deploy. Open the Vercel URL, click **Try AI Stylist** — the floating
   panel now loads the live Streamlit chatbot.

### Local testing of this same setup

You can test the iframe embed locally too: run `streamlit run app.py` in
`streamlit_app/` (port 8501 by default), set
`window.VESTIR_STREAMLIT_URL = "http://localhost:8501"` in `index.html`,
then serve `frontend/` as usual.

## Security note

The API key lives **only** in `backend/.env`, which is excluded from git by
`.gitignore`. The frontend never holds, sends, or displays the key — it only
talks to your own backend, which attaches the key server-side when calling
Groq. If you ever paste a real key into `.env.example` or commit `.env` by
mistake, rotate the key immediately.

## Future improvements

- Persist conversation history per user (currently in-memory in the browser
  tab only).
- Optional image upload so Vestir can comment on an actual outfit photo.
- Streaming responses for a faster perceived reply time.
- Saved "looks" and a personal style profile.

## Screenshots

_Add screenshots of the landing page and chat widget here._
