function escapeHtml(value) {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function formatBotText(text) {
  if (!text) return "";
  const safe = escapeHtml(text);
  const bolded = safe.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  const lines = bolded.split(/\r?\n/);
  const paragraphs = [];
  const listItems = [];
  let current = [];

  lines.forEach((line) => {
    const trimmed = line.trim();
    const isBullet = /^[-*]\s+/.test(trimmed);
    if (!trimmed) {
      if (current.length) {
        paragraphs.push(current.join(" "));
        current = [];
      }
      return;
    }
    if (isBullet) {
      if (current.length) {
        paragraphs.push(current.join(" "));
        current = [];
      }
      listItems.push(trimmed.replace(/^[-*]\s+/, ""));
      return;
    }
    current.push(trimmed);
  });

  if (current.length) {
    paragraphs.push(current.join(" "));
  }

  const html = [];
  paragraphs.forEach((p) => html.push(`<p>${p}</p>`));
  if (listItems.length) {
    html.push("<ul class=\"concierge-list\">");
    listItems.forEach((item) => html.push(`<li>${item}</li>`));
    html.push("</ul>");
  }
  return html.join("");
}

function appendMessage(threadEl, role, content, asHtml) {
  const row = document.createElement("div");
  row.className = `concierge-message concierge-message--${role}`;

  if (role === "bot") {
    const avatar = document.createElement("div");
    avatar.className = "concierge-avatar concierge-avatar--bot";
    avatar.innerHTML = "<img src=\"/static/images/logo.png\" alt=\"SafePaws\">";
    row.appendChild(avatar);
  } else {
    const avatar = document.createElement("div");
    avatar.className = "concierge-avatar concierge-avatar--user";
    avatar.textContent = "You";
    row.appendChild(avatar);
  }

  const bubble = document.createElement("div");
  bubble.className = `concierge-bubble concierge-bubble--${role}`;
  if (asHtml) {
    bubble.innerHTML = content;
  } else {
    bubble.textContent = content;
  }
  row.appendChild(bubble);
  threadEl.appendChild(row);
  threadEl.scrollTop = threadEl.scrollHeight;
  return bubble;
}

async function askConcierge() {
  const input = document.getElementById("conciergeInput");
  const threadEl = document.getElementById("conciergeThread");
  const resultsEl = document.getElementById("conciergeResults");
  if (!input || !threadEl || !resultsEl) return;

  const query = input.value.trim();
  if (!query) return;

  appendMessage(threadEl, "user", query, false);
  input.value = "";
  const loadingBubble = appendMessage(
    threadEl,
    "bot",
    window.I18N ? window.I18N.t("common_searching") : "Searching...",
    false
  );
  resultsEl.innerHTML = "";

  try {
    const res = await fetch("/ai/concierge", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      loadingBubble.textContent = err.message || "Request failed";
      return;
    }
    const data = await res.json();
    const formatted = formatBotText(data.answer || "Here are some options:");
    loadingBubble.innerHTML = formatted || escapeHtml(data.answer || "");

    if (data.mode === "general") {
      resultsEl.innerHTML = "";
      return;
    }

    if (!data.results || !data.results.length) {
      const msg = window.I18N ? window.I18N.t("concierge_no_match") : "No matching providers found. Try another search.";
      resultsEl.innerHTML = `<div class=\"concierge-result\">${escapeHtml(msg)}</div>`;
      return;
    }

    data.results.forEach((r) => {
      const card = document.createElement("div");
      card.className = "concierge-result";
      const price =
        r.price_per_day !== null && r.price_per_day !== undefined
          ? `${r.price_per_day} TND/day`
          : "Price on request";
      const distance = r.distance_km != null ? ` • ${r.distance_km.toFixed(1)} km` : "";
      const providerLink = r.provider_id
        ? `<a href="/provider?id=${r.provider_id}">View provider profile</a>`
        : "";
      const highlights = r.highlights
        ? `<div class="concierge-highlight">${escapeHtml(r.highlights)}</div>`
        : "";
      card.innerHTML = `<strong>${escapeHtml(r.name)}</strong> • ${escapeHtml(
        r.location || ""
      )}<br>${price}${distance}${highlights}<br>${providerLink}`;
      resultsEl.appendChild(card);
    });
  } catch (e) {
    loadingBubble.textContent = "Network error";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const btn = document.getElementById("conciergeBtn");
  const input = document.getElementById("conciergeInput");
  if (btn) btn.addEventListener("click", askConcierge);
  if (input)
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") askConcierge();
    });
});
