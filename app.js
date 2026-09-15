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
    data = { generated_at: null, source_count: 0, article_count: 0, items: [] };
  }

  const timestampEl = document.getElementById("timestamp");
  if (data.generated_at) {
    const d = new Date(data.generated_at);
    timestampEl.textContent =
      "Last updated: " +
      d.toISOString().replace("T", " ").slice(0, 19) +
      " UTC";
  } else {
    timestampEl.textContent = "No data yet. Run the scraper first.";
  }

  const subtitleEl = document.getElementById("subtitle");
  if (subtitleEl) {
    subtitleEl.textContent =
      data.source_count +
      " sources \u00b7 " +
      data.article_count +
      " articles \u00b7 7 days";
  }

  const types = [...new Set(data.items.map(function (i) { return i.type; }))].sort();
  const filtersEl = document.getElementById("filters");
  var activeFilter = null;

  types.forEach(function (t, idx) {
    var btn = document.createElement("button");
    btn.className = "filter-pill";
    btn.dataset.type = t;
    btn.dataset.color = COLORS[idx % COLORS.length];
    btn.textContent = t.toUpperCase();
    btn.addEventListener("click", function () {
      if (activeFilter === t) {
        activeFilter = null;
        btn.classList.remove("active");
      } else {
        activeFilter = t;
        filtersEl.querySelectorAll(".filter-pill").forEach(function (b) {
          b.classList.remove("active");
        });
        btn.classList.add("active");
      }
      applyFilter();
    });
    filtersEl.appendChild(btn);
  });

  var cardsEl = document.getElementById("cards");

  function relativeTime(isoStr) {
    if (!isoStr) return "";
    var diff = Date.now() - new Date(isoStr).getTime();
    var mins = Math.floor(diff / 60000);
    if (mins < 1) return "just now";
    if (mins < 60) return mins + "m ago";
    var hrs = Math.floor(mins / 60);
    if (hrs < 24) return hrs + "h ago";
    var days = Math.floor(hrs / 24);
    return days + "d ago";
  }

  function renderCards() {
    cardsEl.innerHTML = "";
    data.items.forEach(function (item, idx) {
      var colorIdx = idx % COLORS.length;
      var cardColor = COLOR_MAP[COLORS[colorIdx]];
      var card = document.createElement("div");
      card.className = "card";
      card.dataset.type = item.type;
      card.style.setProperty("--card-color", cardColor);
      card.style.animationDelay = idx * 40 + "ms";

      var desc = item.description
        ? '<p class="description">' + escapeHtml(item.description) + "</p>"
        : "";

      card.innerHTML =
        '<span class="type-badge">' +
        escapeHtml(item.type.toUpperCase()) +
        "</span>" +
        '<span class="source-tag">' +
        escapeHtml(item.source) +
        "</span>" +
        "<h3>" + escapeHtml(item.title) + "</h3>" +
        desc +
        '<div class="meta">' +
        '<a href="' +
        escapeHtml(item.url) +
        '" target="_blank" rel="noopener">Read more \u2192</a>' +
        "<time>" +
        relativeTime(data.generated_at) +
        "</time>" +
        "</div>";
      cardsEl.appendChild(card);
    });
  }

  function applyFilter() {
    document.querySelectorAll(".card").forEach(function (card) {
      if (!activeFilter || card.dataset.type === activeFilter) {
        card.style.display = "";
      } else {
        card.style.display = "none";
      }
    });
  }

  function escapeHtml(str) {
    var div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  renderCards();
})();
