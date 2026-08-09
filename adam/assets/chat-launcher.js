(function () {
  "use strict";

  // Don't render the launcher on the standalone chat page.
  if (location.pathname.replace(/\/$/, "") === "/adam/chat") return;
  // Only show under /adam/. The root is a landing shell.
  if (!location.pathname.startsWith("/adam/")) return;

  const LS_DISMISSED = "wos_chat_dismissed_v1";
  const LS_FIRST_SEEN = "wos_chat_first_seen_v1";
  const MAX_CHARS = 2000;
  const TEASER_DELAY_MS = 4000;

  // Guard against environments where localStorage throws (private mode, blocked storage, etc.)
  const safeLS = (function () {
    try {
      const t = "__wos_probe__";
      localStorage.setItem(t, "1");
      localStorage.removeItem(t);
      return {
        get: (k) => { try { return localStorage.getItem(k); } catch (_) { return null; } },
        set: (k, v) => { try { localStorage.setItem(k, v); } catch (_) {} },
      };
    } catch (_) {
      const mem = {};
      return {
        get: (k) => (k in mem ? mem[k] : null),
        set: (k, v) => { mem[k] = v; },
      };
    }
  })();

  if (safeLS.get(LS_DISMISSED) === "1") return;

  function el(tag, attrs, children) {
    const n = document.createElement(tag);
    if (attrs) for (const k in attrs) {
      if (k === "class") n.className = attrs[k];
      else if (k === "text") n.textContent = attrs[k];
      else if (k.startsWith("on") && typeof attrs[k] === "function") n.addEventListener(k.slice(2), attrs[k]);
      else n.setAttribute(k, attrs[k]);
    }
    if (children) children.forEach(c => c && n.appendChild(c));
    return n;
  }

  function escapeHtml(s) {
    return s.replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;" })[c]);
  }
  function linkifyPaths(text) {
    return text.replace(/(\/adam\/[a-z0-9\-/.#]+[a-z0-9])/gi, m => '<a href="' + m + '">' + m + '</a>');
  }

  // ---- DOM ----
  // The launcher root is a normal interactive region (contains the trigger pill).
  // The dialog inside is aria-modal and toggled via [hidden]; do NOT aria-hide
  // the root or screen readers can't reach the pill or the open dialog.
  const root = el("div", { class: "wos-chat-root" });

  const pill = el("button", {
    class: "wos-chat-pill",
    type: "button",
    "aria-label": "Open chat: Ask about Adam",
    "aria-expanded": "false",
  });
  pill.appendChild(el("span", { class: "wos-chat-pill-icon", "aria-hidden": "true", text: "\u{1F4AC}" }));
  pill.appendChild(el("span", { class: "wos-chat-pill-label", text: "Ask about Adam" }));

  const teaser = el("div", { class: "wos-chat-teaser", role: "status", "aria-live": "polite" });
  teaser.appendChild(el("span", { class: "wos-chat-teaser-text", text: "Ask me anything about Adam." }));
  const teaserClose = el("button", {
    class: "wos-chat-teaser-close",
    type: "button",
    "aria-label": "Dismiss",
    text: "\u00d7",
  });
  teaser.appendChild(teaserClose);

  const panel = el("div", {
    class: "wos-chat-panel",
    role: "dialog",
    "aria-modal": "true",
    "aria-labelledby": "wos-chat-title",
    hidden: "",
  });

  const header = el("div", { class: "wos-chat-header" });
  header.appendChild(el("h2", { id: "wos-chat-title", class: "wos-chat-title", text: "Ask about Adam" }));
  const headerRight = el("div", { class: "wos-chat-header-right" });
  const fullBtn = el("a", { class: "wos-chat-full", href: "/adam/chat/", text: "Full page \u2197", "aria-label": "Open full chat page" });
  const closeBtn = el("button", { class: "wos-chat-close", type: "button", "aria-label": "Close chat", text: "\u00d7" });
  headerRight.appendChild(fullBtn);
  headerRight.appendChild(closeBtn);
  header.appendChild(headerRight);

  const messages = el("div", {
    class: "wos-chat-messages",
    id: "wos-chat-messages",
    "aria-live": "polite",
    "aria-label": "Conversation",
  });

  const greeting = el("div", { class: "wos-chat-msg wos-chat-msg-assistant" });
  const gbubble = el("div", { class: "wos-chat-bubble" });
  gbubble.innerHTML = "Hi! I'm a small assistant grounded in this site's content. Ask about Adam's work, patents, or philosophy. For anything else, try the <a href=\"/adam/contact/\">contact page</a>.";
  greeting.appendChild(gbubble);
  messages.appendChild(greeting);

  const form = el("form", { class: "wos-chat-form", autocomplete: "off" });
  const inputLabel = el("label", { for: "wos-chat-input", class: "wos-chat-visually-hidden", text: "Your question" });
  const input = el("textarea", {
    id: "wos-chat-input",
    class: "wos-chat-input",
    name: "message",
    rows: "2",
    maxlength: String(MAX_CHARS),
    placeholder: "Ask a question...",
    required: "",
  });
  const controls = el("div", { class: "wos-chat-controls" });
  const status = el("div", { class: "wos-chat-status", id: "wos-chat-status", "aria-live": "polite" });
  const submit = el("button", { class: "wos-chat-submit", type: "submit", text: "Ask" });
  controls.appendChild(status);
  controls.appendChild(submit);
  form.appendChild(inputLabel);
  form.appendChild(input);
  form.appendChild(controls);

  panel.appendChild(header);
  panel.appendChild(messages);
  panel.appendChild(form);

  root.appendChild(teaser);
  root.appendChild(pill);
  root.appendChild(panel);

  document.addEventListener("DOMContentLoaded", () => document.body.appendChild(root));

  // ---- teaser scheduling ----
  const firstSeen = safeLS.get(LS_FIRST_SEEN);
  if (!firstSeen) {
    setTimeout(() => {
      if (panel.hasAttribute("hidden") && safeLS.get(LS_DISMISSED) !== "1") {
        teaser.classList.add("wos-chat-teaser-visible");
      }
    }, TEASER_DELAY_MS);
    safeLS.set(LS_FIRST_SEEN, "1");
  }
  teaserClose.addEventListener("click", (e) => {
    e.stopPropagation();
    teaser.classList.remove("wos-chat-teaser-visible");
  });
  teaser.addEventListener("click", (e) => {
    if (e.target === teaserClose) return;
    teaser.classList.remove("wos-chat-teaser-visible");
    openPanel();
  });

  // ---- open/close ----
  let previouslyFocused = null;
  function openPanel() {
    previouslyFocused = document.activeElement;
    panel.removeAttribute("hidden");
    panel.classList.add("wos-chat-panel-open");
    pill.setAttribute("aria-expanded", "true");
    teaser.classList.remove("wos-chat-teaser-visible");
    setTimeout(() => input.focus(), 30);
    document.addEventListener("keydown", onKeydown);
  }
  function closePanel(dismissForever) {
    panel.setAttribute("hidden", "");
    panel.classList.remove("wos-chat-panel-open");
    pill.setAttribute("aria-expanded", "false");
    document.removeEventListener("keydown", onKeydown);
    if (previouslyFocused && previouslyFocused.focus) previouslyFocused.focus();
    if (dismissForever) {
      safeLS.set(LS_DISMISSED, "1");
      root.remove();
    }
  }
  function onKeydown(ev) {
    if (ev.key === "Escape") { ev.preventDefault(); closePanel(false); }
    if (ev.key === "Tab") {
      const focusables = panel.querySelectorAll("a,button,textarea,input,select,[tabindex]:not([tabindex=\"-1\"])");
      if (!focusables.length) return;
      const first = focusables[0];
      const last = focusables[focusables.length - 1];
      if (ev.shiftKey && document.activeElement === first) { ev.preventDefault(); last.focus(); }
      else if (!ev.shiftKey && document.activeElement === last) { ev.preventDefault(); first.focus(); }
    }
  }
  pill.addEventListener("click", () => {
    if (panel.hasAttribute("hidden")) openPanel(); else closePanel(false);
  });
  closeBtn.addEventListener("click", () => closePanel(false));

  // ---- streaming ----
  function appendMessage(role, text) {
    const wrap = el("div", { class: "wos-chat-msg wos-chat-msg-" + role });
    const bubble = el("div", { class: "wos-chat-bubble", text: text });
    wrap.appendChild(bubble);
    messages.appendChild(wrap);
    messages.scrollTop = messages.scrollHeight;
    return bubble;
  }
  function setBusy(busy) {
    submit.disabled = busy;
    input.disabled = busy;
    status.textContent = busy ? "Thinking..." : "";
  }
  async function streamResponse(userText, bubble) {
    const errorMap = {
      rate_limit_minute: "Slow down a bit \u2014 too many questions in the last minute.",
      rate_limit_hour: "You've hit the hourly limit for this IP. Try again later.",
      daily_budget_exhausted: "The site's daily chat budget is used up. Try again tomorrow, or email Adam directly.",
      message_too_long: "That question is too long. Please keep it under " + MAX_CHARS + " characters.",
      empty_message: "Please type a question first.",
      invalid_chars: "Your message contains characters I can't accept.",
      invalid_json: "Something went wrong sending your question.",
    };
    let acc = "";
    try {
      const resp = await fetch("/adam/chat/api/message", {
        method: "POST",
        headers: { "Content-Type": "application/json", "Accept": "text/event-stream" },
        body: JSON.stringify({ message: userText }),
      });
      if (!resp.ok) {
        let msg = "Something went wrong (HTTP " + resp.status + ").";
        try {
          const body = await resp.json();
          if (body && body.error) msg = errorMap[body.error] || ("Error: " + body.error);
        } catch (_) {}
        bubble.textContent = msg;
        return;
      }
      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let buf = "";
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });
        const frames = buf.split("\n\n");
        buf = frames.pop() || "";
        for (const frame of frames) {
          let evt = "message", data = "";
          for (const line of frame.split("\n")) {
            if (line.startsWith("event:")) evt = line.slice(6).trim();
            else if (line.startsWith("data:")) data += line.slice(5).trim();
          }
          if (!data) continue;
          let parsed;
          try { parsed = JSON.parse(data); } catch (_) { continue; }
          const payload = parsed.data || "";
          if (evt === "token") {
            acc += payload;
            bubble.textContent = acc;
            messages.scrollTop = messages.scrollHeight;
          } else if (evt === "error") {
            bubble.textContent = payload || "The assistant is unavailable right now.";
          } else if (evt === "done") {
            bubble.innerHTML = linkifyPaths(escapeHtml(acc));
          }
        }
      }
    } catch (err) {
      bubble.textContent = "Network error \u2014 please try again.";
    }
  }
  form.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const text = input.value.trim();
    if (!text) return;
    if (text.length > MAX_CHARS) {
      appendMessage("system", "Question is too long. Keep it under " + MAX_CHARS + " characters.");
      return;
    }
    appendMessage("user", text);
    input.value = "";
    const bubble = appendMessage("assistant", "\u2026");
    setBusy(true);
    try { await streamResponse(text, bubble); }
    finally { setBusy(false); input.focus(); }
  });
  input.addEventListener("keydown", (ev) => {
    if (ev.key === "Enter" && !ev.shiftKey) { ev.preventDefault(); form.requestSubmit(); }
  });
})();
