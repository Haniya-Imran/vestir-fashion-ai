"""
app.py
------
Vestir — AI Fashion Stylist, as a standalone Streamlit app.

This is the "backend" the teacher asked for on Streamlit Cloud: it IS the
chatbot (Streamlit apps serve their own UI, they don't expose a separate
JSON API), styled to match the Vercel-hosted landing page so the two feel
like one product when the landing page embeds this app in an iframe.

Run locally:
    streamlit run app.py
"""

import streamlit as st
from stylist_engine import generate_reply, is_configured, UpstreamError

st.set_page_config(
    page_title="Vestir — AI Fashion Stylist",
    page_icon="✨",
    layout="centered",
)

QUICK_ACTIONS = [
    ("✨ Style an Outfit", "Help me create a stylish outfit. Ask me about the occasion, season, colors, and clothing items I have."),
    ("👗 Outfit Ideas", "Give me a few outfit ideas I can try this week."),
    ("🎨 Match My Colors", "Help me find colors that match well for an outfit."),
    ("💍 Accessory Ideas", "What accessories would work well with my outfit?"),
    ("👠 Dress for an Occasion", "Help me choose an outfit for a specific occasion."),
    ("🧥 Build a Look", "Help me build a complete look from scratch."),
]

# ---------------------------------------------------------------------
# Theme: mirror the Vestir pink / cream / charcoal design system
# ---------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fraunces:wght@500;600&family=Inter:wght@400;500;600&display=swap');

    html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }
    .stApp { background: #FAF5F0; }

    .vestir-header {
        display: flex; align-items: center; gap: 12px;
        padding: 6px 0 18px; border-bottom: 1px solid #EFE9E3; margin-bottom: 18px;
    }
    .vestir-badge {
        width: 40px; height: 40px; border-radius: 50%; flex-shrink: 0;
        background: linear-gradient(135deg, #C68A93, #7A3F4A);
        display: flex; align-items: center; justify-content: center;
        color: white; font-size: 18px;
    }
    .vestir-title { font-family: 'Fraunces', serif; font-size: 1.3rem; font-weight: 600; color: #2B2420; margin: 0; }
    .vestir-sub { font-size: 0.8rem; color: #A85D6B; margin: 0; display:flex; align-items:center; gap:5px;}
    .vestir-sub::before { content: ""; width: 6px; height: 6px; border-radius: 50%; background: #7FDB9E; display:inline-block; }

    .welcome-box {
        background: linear-gradient(160deg, #EFD9D3, #F3EAE3);
        border-radius: 16px; padding: 18px 20px; margin-bottom: 16px;
    }
    .welcome-box h4 { font-family: 'Fraunces', serif; margin: 0 0 6px; color: #2B2420; }
    .welcome-box p { margin: 0; color: #7A3F4A; font-size: 0.92rem; }

    div[data-testid="stChatMessage"] { padding: 4px 0; }

    .stButton>button {
        border-radius: 12px; border: 1px solid #EFE9E3; background: white;
        color: #2B2420; font-size: 0.85rem; text-align: left; padding: 10px 12px;
    }
    .stButton>button:hover { border-color: #C68A93; color: #7A3F4A; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="vestir-header">
        <div class="vestir-badge">✨</div>
        <div>
            <p class="vestir-title">Vestir</p>
            <p class="vestir-sub">AI Stylist</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if not is_configured():
    st.warning(
        "This app isn't connected to the styling service yet. "
        "Add **GROQ_API_KEY** in *Settings → Secrets* on Streamlit Cloud "
        "(or in `.streamlit/secrets.toml` locally), then rerun.",
        icon="⚠️",
    )

if "messages" not in st.session_state:
    st.session_state.messages = []  # [{"role": "user"|"assistant", "content": str}]

# ---------------------------------------------------------------------
# Welcome state + fashion-only quick actions (only before the first message)
# ---------------------------------------------------------------------
pending_prompt = None

if not st.session_state.messages:
    st.markdown(
        """
        <div class="welcome-box">
            <h4>Hi! I'm your AI Fashion Stylist ✨</h4>
            <p>Tell me what you're looking for and I'll help you style it.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    cols = st.columns(2)
    for i, (label, prompt) in enumerate(QUICK_ACTIONS):
        if cols[i % 2].button(label, use_container_width=True, key=f"qa_{i}"):
            pending_prompt = prompt

# ---------------------------------------------------------------------
# Render conversation so far
# ---------------------------------------------------------------------
for msg in st.session_state.messages:
    avatar = "✨" if msg["role"] == "assistant" else "🧑"
    with st.chat_message(msg["role"], avatar=avatar):
        st.write(msg["content"])

# ---------------------------------------------------------------------
# Input (typed message or a clicked quick action)
# ---------------------------------------------------------------------
typed_prompt = st.chat_input("Ask your AI stylist...")
user_prompt = pending_prompt or typed_prompt

if user_prompt:
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user", avatar="🧑"):
        st.write(user_prompt)

    with st.chat_message("assistant", avatar="✨"):
        with st.spinner("Styling your look..."):
            try:
                reply = generate_reply(user_prompt, st.session_state.messages[:-1])
                st.write(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
            except UpstreamError as exc:
                st.error(str(exc), icon="🚫")
                if st.button("Try again", key=f"retry_{len(st.session_state.messages)}"):
                    st.rerun()

# ---------------------------------------------------------------------
# New chat control
# ---------------------------------------------------------------------
if st.session_state.messages:
    if st.button("↻ New chat", key="new_chat"):
        st.session_state.messages = []
        st.rerun()
