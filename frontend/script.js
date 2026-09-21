/* =========================================================
   VESTIR — frontend logic
   Talks to the backend at /chat (see backend/main.py).
   No API key ever appears in this file — the backend holds it.
   ========================================================= */

(() => {
  "use strict";

  // Backend base URL. Same-origin by default; override by serving
  // frontend behind a proxy, or set window.VESTIR_API_BASE before this script.
  const API_BASE = window.VESTIR_API_BASE || "http://127.0.0.1:8000";

  // If the chatbot is deployed as a Streamlit app (e.g. on Streamlit
  // Community Cloud), set this to its URL before script.js loads:
  //   <script>window.VESTIR_STREAMLIT_URL = "https://your-app.streamlit.app";</script>
  // When set, the floating panel embeds that app directly instead of
  // talking to the FastAPI /chat endpoint — Streamlit apps serve their
  // own UI, so there is no separate JSON API to call from here.
  const STREAMLIT_URL = window.VESTIR_STREAMLIT_URL || "";

  // ---------- Nav ----------
  const navToggle = document.getElementById("navToggle");
  const mobileMenu = document.getElementById("mobileMenu");
  navToggle?.addEventListener("click", () => {
    const open = mobileMenu.classList.toggle("open");
    navToggle.setAttribute("aria-expanded", String(open));
  });
  mobileMenu?.querySelectorAll("a").forEach((a) =>
    a.addEventListener("click", () => {
      mobileMenu.classList.remove("open");
      navToggle.setAttribute("aria-expanded", "false");
    })
  );

  // ---------- Chat widget elements ----------
  const launcher = document.getElementById("chatLauncher");
  const panel = document.getElementById("chatPanel");
  const closeBtn = document.getElementById("chatCloseBtn");
  const body = document.getElementById("chatBody");
  const form = document.getElementById("chatForm");
  const input = document.getElementById("chatInput");
  const sendBtn = document.getElementById("sendBtn");
  const menuToggle = document.getElementById("chatMenuToggle");
  const menu = document.getElementById("chatMenu");
  const newChatBtn = document.getElementById("newChatBtn");

  const QUICK_ACTIONS = [
    { icon: "✨", label: "Style an Outfit", prompt: "Help me create a stylish outfit. Ask me about the occasion, season, colors, and clothing items I have." },
    { icon: "👗", label: "Outfit Ideas", prompt: "Give me a few outfit ideas I can try this week." },
    { icon: "🎨", label: "Match My Colors", prompt: "Help me find colors that match well for an outfit." },
    { icon: "💍", label: "Accessory Ideas", prompt: "What accessories would work well with my outfit?" },
    { icon: "👠", label: "Dress for an Occasion", prompt: "Help me choose an outfit for a specific occasion." },
    { icon: "🧥", label: "Build a Look", prompt: "Help me build a complete look from scratch." },
  ];

  // conversation state: [{ role: 'user' | 'assistant', content: string }]
  let history = [];
  let isSending = false;

  function renderWelcome() {
    body.innerHTML = "";
    const welcome = document.createElement("div");
    welcome.className = "welcome-card";
    welcome.innerHTML = `
      <svg class="w-mark" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
        <circle cx="20" cy="20" r="20" fill="url(#welcomeGrad)"/>
        <path d="M20 9c-1.4 0-2.5 1.1-2.5 2.5 0 .6.2 1.1.5 1.5l-6 4.6c-1.1.8-1.7 2.1-1.5 3.4L11.6 29a1.5 1.5 0 0 0 1.5 1.3h13.8a1.5 1.5 0 0 0 1.5-1.3l1.1-7.9c.2-1.3-.4-2.6-1.5-3.4l-6-4.6c.3-.4.5-.9.5-1.5C22.5 10.1 21.4 9 20 9z" stroke="#FAF5F0" stroke-width="1.3" stroke-linejoin="round"/>
        <defs><linearGradient id="welcomeGrad" x1="0" y1="0" x2="40" y2="40" gradientUnits="userSpaceOnUse"><stop stop-color="#C68A93"/><stop offset="1" stop-color="#7A3F4A"/></linearGradient></defs>
      </svg>
      <h3>Hi! I'm your AI Fashion Stylist ✨</h3>
      <p>Tell me what you're looking for and I'll help you style it.</p>
    `;
    body.appendChild(welcome);

    const grid = document.createElement("div");
    grid.className = "quick-actions";
    QUICK_ACTIONS.forEach((qa) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "qa-btn";
      btn.innerHTML = `<span aria-hidden="true">${qa.icon}</span><span>${qa.label}</span>`;
      btn.addEventListener("click", () => sendMessage(qa.prompt));
      grid.appendChild(btn);
    });
    body.appendChild(grid);
  }

  function avatarSVG(kind) {
    if (kind === "user") {
      return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="8" r="4"/><path d="M4 21c0-4.4 3.6-8 8-8s8 3.6 8 8"/></svg>`;
    }
    return `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2l1.8 5.4L19 9l-5.2 1.6L12 16l-1.8-5.4L5 9l5.2-1.6L12 2z"/></svg>`;
  }

  function appendMessage(role, text) {
    const row = document.createElement("div");
    row.className = `msg-row ${role === "user" ? "from-user" : "from-ai"}`;

    const avatar = document.createElement("div");
    avatar.className = `msg-avatar ${role === "user" ? "user-avatar" : ""}`;
    avatar.innerHTML = avatarSVG(role);

    const col = document.createElement("div");
    col.className = "msg-col";

    const bubble = document.createElement("div");
    bubble.className = "bubble";
    bubble.textContent = text;
    col.appendChild(bubble);

    if (role === "assistant") {
      const actions = document.createElement("div");
      actions.className = "msg-actions";
      actions.innerHTML = `
        <button type="button" data-action="copy" aria-label="Copy response">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="9" y="9" width="12" height="12" rx="2"/><path d="M5 15V5a2 2 0 012-2h10"/></svg>
        </button>
        <button type="button" data-action="regenerate" aria-label="Regenerate response">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M21 12a9 9 0 11-3-6.7"/><path d="M21 3v6h-6"/></svg>
        </button>
      `;
      actions.querySelector('[data-action="copy"]').addEventListener("click", () => {
        navigator.clipboard?.writeText(text);
      });
      actions.querySelector('[data-action="regenerate"]').addEventListener("click", () => {
        regenerateLast();
      });
      col.appendChild(actions);
    }

    row.appendChild(avatar);
    row.appendChild(col);
    body.appendChild(row);
    scrollToBottom();
  }

  function scrollToBottom() {
    requestAnimationFrame(() => { body.scrollTop = body.scrollHeight; });
  }

  function showTyping() {
    const row = document.createElement("div");
    row.className = "typing-row";
    row.id = "typingRow";
    row.innerHTML = `
      <div class="msg-avatar">${avatarSVG("assistant")}</div>
      <div class="typing-dots"><span></span><span></span><span></span></div>
    `;
    body.appendChild(row);
    scrollToBottom();
  }

  function hideTyping() {
    document.getElementById("typingRow")?.remove();
  }

  function showError(message, retryFn) {
    const row = document.createElement("div");
    row.className = "error-row";
    row.innerHTML = `<div>${message}</div>`;
    const retry = document.createElement("button");
    retry.type = "button";
    retry.textContent = "Try again";
    retry.addEventListener("click", () => {
      row.remove();
      retryFn();
    });
    row.appendChild(document.createElement("br"));
    row.appendChild(retry);
    body.appendChild(row);
    scrollToBottom();
  }

  let lastUserMessage = null;

  async function sendMessage(text) {
    const trimmed = text.trim();
    if (!trimmed || isSending) return;

    // first real message clears the welcome/quick-actions state
    if (history.length === 0) {
      body.innerHTML = "";
    }

    appendMessage("user", trimmed);
    history.push({ role: "user", content: trimmed });
    lastUserMessage = trimmed;
    input.value = "";
    autoGrow();
    await requestReply();
  }

  async function requestReply() {
    isSending = true;
    sendBtn.disabled = true;
    showTyping();

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: lastUserMessage, history }),
      });

      if (!res.ok) {
        const errBody = await res.json().catch(() => ({}));
        throw new Error(errBody.detail || `Request failed (${res.status})`);
      }

      const data = await res.json();
      hideTyping();
      const reply = data.reply || "I couldn't come up with a reply just now — could you try rephrasing?";
      appendMessage("assistant", reply);
      history.push({ role: "assistant", content: reply });
    } catch (err) {
      hideTyping();
      showError(
        "Vestir couldn't reach the styling service. Check that the backend is running.",
        requestReply
      );
    } finally {
      isSending = false;
      sendBtn.disabled = false;
    }
  }

  function regenerateLast() {
    if (!lastUserMessage || isSending) return;
    // drop the last assistant turn from history before retrying
    if (history.length && history[history.length - 1].role === "assistant") {
      history.pop();
    }
    requestReply();
  }

  // ---------- Streamlit embed mode ----------
  // Swaps the custom chat UI for an iframe pointing at the deployed
  // Streamlit app. Runs once at load if VESTIR_STREAMLIT_URL is set.
  function setupStreamlitEmbed() {
    const foot = document.querySelector(".chat-foot");
    body.innerHTML = "";
    body.style.padding = "0";

    const iframe = document.createElement("iframe");
    iframe.src = STREAMLIT_URL;
    iframe.title = "Vestir AI Stylist";
    iframe.style.width = "100%";
    iframe.style.height = "100%";
    iframe.style.border = "none";
    iframe.loading = "lazy";
    body.appendChild(iframe);

    foot?.remove(); // Streamlit renders its own chat input inside the iframe
    menuToggle?.closest(".chat-head-actions")?.querySelector("#chatMenuToggle")?.remove();
  }

  // ---------- Panel open/close ----------
  function openPanel() {
    panel.classList.add("is-open");
    panel.setAttribute("aria-hidden", "false");
    launcher.classList.add("is-open");
    launcher.setAttribute("aria-expanded", "true");
    if (!STREAMLIT_URL && history.length === 0) renderWelcome();
    if (!STREAMLIT_URL) input.focus();
  }
  function closePanel() {
    panel.classList.remove("is-open");
    panel.setAttribute("aria-hidden", "true");
    launcher.classList.remove("is-open");
    launcher.setAttribute("aria-expanded", "false");
    menu.classList.remove("open");
  }
  function togglePanel() {
    panel.classList.contains("is-open") ? closePanel() : openPanel();
  }

  launcher.addEventListener("click", togglePanel);
  closeBtn.addEventListener("click", closePanel);
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && panel.classList.contains("is-open")) closePanel();
  });

  ["navTryStylist", "mobileTryStylist", "heroTryStylist", "ctaTryStylist", "footerTryStylist"].forEach((id) => {
    document.getElementById(id)?.addEventListener("click", (e) => {
      e.preventDefault();
      openPanel();
    });
  });

  // ---------- Menu (new chat) ----------
  menuToggle.addEventListener("click", (e) => {
    e.stopPropagation();
    const open = menu.classList.toggle("open");
    menuToggle.setAttribute("aria-expanded", String(open));
  });
  document.addEventListener("click", (e) => {
    if (!menu.contains(e.target) && e.target !== menuToggle) menu.classList.remove("open");
  });
  newChatBtn.addEventListener("click", () => {
    history = [];
    lastUserMessage = null;
    menu.classList.remove("open");
    renderWelcome();
  });

  // ---------- Input form ----------
  function autoGrow() {
    input.style.height = "auto";
    input.style.height = Math.min(input.scrollHeight, 90) + "px";
  }
  input.addEventListener("input", autoGrow);
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      form.requestSubmit();
    }
  });
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    sendMessage(input.value);
  });

  // ---------- Init ----------
  if (STREAMLIT_URL) setupStreamlitEmbed();

})();
