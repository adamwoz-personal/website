(function () {
  "use strict";

  const form = document.getElementById("chat-form");
  const input = document.getElementById("chat-input");
  const messagesEl = document.getElementById("chat-messages");
  const statusEl = document.getElementById("chat-status");
  const submitBtn = document.getElementById("chat-submit");
  const MAX_CHARS = 2000;

  function escapeHtml(s) {
    return s.replace(/[&<>"']/g, function (c) {
      return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;" })[c];
    });
  }

  function linkifyPaths(text) {
    return text.replace(/(\/adam\/[a-z0-9\-/.#]+[a-z0-9])/gi, function (m) {
      return '<a href="' + m + '">' + m + "</a>";
    });
  }

  function appendMessage(role, text) {
    const wrap = document.createElement("div");
    wrap.className = "chat-msg chat-msg-" + role;
    const bubble = document.createElement("div");
    bubble.className = "chat-bubble";
    bubble.textContent = text;
    wrap.appendChild(bubble);
    messagesEl.appendChild(wrap);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return bubble;
  }

  function setBusy(busy) {
    submitBtn.disabled = busy;
    input.disabled = busy;
    statusEl.textContent = busy ? "Thinking..." : "";
  }

  async function streamResponse(userText, bubble) {
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
          if (body && body.error) {
            const map = {
              rate_limit_minute: "Slow down a bit \u2014 too many questions in the last minute.",
              rate_limit_hour: "You've hit the hourly limit for this IP. Try again later.",
              daily_budget_exhausted: "The site's daily chat budget is used up. Try again tomorrow, or email Adam directly.",
              message_too_long: "That question is too long. Please keep it under " + MAX_CHARS + " characters.",
              empty_message: "Please type a question first.",
              invalid_chars: "Your message contains characters I can't accept.",
              invalid_json: "Something went wrong sending your question.",
            };
            msg = map[body.error] || ("Error: " + body.error);
          }
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
          const lines = frame.split("\n");
          let event = "message";
          let data = "";
          for (const line of lines) {
            if (line.startsWith("event:")) event = line.slice(6).trim();
            else if (line.startsWith("data:")) data += line.slice(5).trim();
          }
          if (!data) continue;
          let parsed;
          try { parsed = JSON.parse(data); } catch (_) { continue; }
          const payload = parsed.data || "";
          if (event === "token") {
            acc += payload;
            bubble.textContent = acc;
            messagesEl.scrollTop = messagesEl.scrollHeight;
          } else if (event === "error") {
            bubble.textContent = payload || "The assistant is unavailable right now.";
          } else if (event === "done") {
            bubble.innerHTML = linkifyPaths(escapeHtml(acc));
          }
        }
      }
    } catch (err) {
      bubble.textContent = "Network error \u2014 please try again.";
    }
  }

  form.addEventListener("submit", async function (ev) {
    ev.preventDefault();
    const text = input.value.trim();
    if (!text) return;
    if (text.length > MAX_CHARS) {
      appendMessage("system", "Question is too long. Keep it under " + MAX_CHARS + " characters.");
      return;
    }
    appendMessage("user", text);
    input.value = "";
    const bubble = appendMessage("assistant", "");
    bubble.textContent = "\u2026";
    setBusy(true);
    try {
      await streamResponse(text, bubble);
    } finally {
      setBusy(false);
      input.focus();
    }
  });

  input.addEventListener("keydown", function (ev) {
    if (ev.key === "Enter" && !ev.shiftKey) {
      ev.preventDefault();
      form.requestSubmit();
    }
  });

  document.querySelectorAll("[data-suggest]").forEach(function (el) {
    el.addEventListener("click", function () {
      input.value = el.getAttribute("data-suggest") || "";
      input.focus();
    });
  });
})();
