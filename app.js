(async function () {
  const COLORS = ["pink", "teal", "yellow", "purple", "orange", "lime"];
  const COLOR_MAP = {
    pink: "var(--memphis-pink)",
    teal: "var(--memphis-teal)",
    yellow: "var(--memphis-yellow)",
    purple: "var(--memphis-purple)",
    orange: "var(--memphis-orange)",
    lime: "var(--memphis-lime)",
  };

  let data;
  try {
    const resp = await fetch("data/summaries.json");
    data = await resp.json();
  } catch {
    data = { generated_at: null, count: 0, items: [] };
  }

  const timestampEl = document.getElementById("timestamp");
  if (data.generated_at) {
    const d = new Date(data.generated_at);
    timestampEl.textContent = "Last updated: " + d.toISOString().replace("T", " ").slice(0, 19) + " UTC";
  } else {
    timestampEl.textContent = "No data yet. Run the scraper first.";
  }

  const types = [...new Set(data.items.map((i) => i.type))].sort();
  const filtersEl = document.getElementById("filters");
  let activeFilter = null;

  types.forEach((t, idx) => {
    const btn = document.createElement("button");
    btn.className = "filter-pill";
    btn.dataset.type = t;
    btn.dataset.color = COLORS[idx % COLORS.length];
    btn.textContent = t.toUpperCase();
    btn.addEventListener("click", () => {
      if (activeFilter === t) {
        activeFilter = null;
        btn.classList.remove("active");
      } else {
        activeFilter = t;
        filtersEl.querySelectorAll(".filter-pill").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
      }
      applyFilter();
    });
    filtersEl.appendChild(btn);
  });

  const cardsEl = document.getElementById("cards");

  function relativeTime(isoStr) {
    if (!isoStr) return "";
    const diff = Date.now() - new Date(isoStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return "just now";
    if (mins < 60) return mins + "m ago";
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return hrs + "h ago";
    const days = Math.floor(hrs / 24);
    return days + "d ago";
  }

  function renderCards() {
    cardsEl.innerHTML = "";
    data.items.forEach((item, idx) => {
      const colorIdx = idx % COLORS.length;
      const cardColor = COLOR_MAP[COLORS[colorIdx]];
      const card = document.createElement("div");
      card.className = "card";
      card.dataset.type = item.type;
      card.style.setProperty("--card-color", cardColor);
      card.style.animationDelay = (idx * 80) + "ms";
      card.innerHTML =
        '<span class="type-badge">' + escapeHtml(item.type.toUpperCase()) + "</span>" +
        "<h3>" + escapeHtml(item.source) + "</h3>" +
        '<p class="summary">' + escapeHtml(item.summary) + "</p>" +
        '<div class="meta">' +
        '<a href="' + escapeHtml(item.url) + '" target="_blank" rel="noopener">Read original \u2192</a>' +
        "<time>" + relativeTime(data.generated_at) + "</time>" +
        "</div>";
      cardsEl.appendChild(card);
    });
  }

  function applyFilter() {
    document.querySelectorAll(".card").forEach((card) => {
      if (!activeFilter || card.dataset.type === activeFilter) {
        card.style.display = "";
      } else {
        card.style.display = "none";
      }
    });
  }

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  renderCards();
})();
