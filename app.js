(async function () {
  var COLORS = ["pink", "teal", "yellow", "purple", "orange", "lime"];
  var COLOR_MAP = {
    pink: "var(--memphis-pink)",
    teal: "var(--memphis-teal)",
    yellow: "var(--memphis-yellow)",
    purple: "var(--memphis-purple)",
    orange: "var(--memphis-orange)",
    lime: "var(--memphis-lime)",
  };
  var CORS_PROXIES = [
    "https://api.allorigins.win/raw?url=",
    "https://corsproxy.io/?url=",
    "https://api.codetabs.com/v1/proxy?quest=",
  ];
  var POLL_INTERVAL = 5 * 60 * 1000;

  var scrapedData = { generated_at: null, source_count: 0, article_count: 0, items: [] };
  var liveItems = [];
  var allItems = [];
  var rssMap = {};
  var researchData = [];
  var activeTab = "news";

  try {
    var resp = await fetch("data/summaries.json");
    scrapedData = await resp.json();
  } catch (e) {}

  try {
    var rssResp = await fetch("data/rss.json");
    rssMap = await rssResp.json();
  } catch (e) {}

  try {
    var papersResp = await fetch("data/papers-latest.json");
    researchData = await papersResp.json();
  } catch (e) {}

  var timestampEl = document.getElementById("timestamp");
  if (scrapedData.generated_at) {
    var d = new Date(scrapedData.generated_at);
    timestampEl.textContent = "Last scrape: " + d.toISOString().replace("T", " ").slice(0, 19) + " UTC";
  } else {
    timestampEl.textContent = "No data yet. Run the scraper first.";
  }

  // ─── TAB SWITCHING ───
  var tabBar = document.getElementById("tab-bar");
  tabBar.addEventListener("click", function (e) {
    var btn = e.target.closest(".tab");
    if (!btn) return;
    var tab = btn.dataset.tab;
    activeTab = tab;
    tabBar.querySelectorAll(".tab").forEach(function (b) { b.classList.remove("active"); });
    btn.classList.add("active");
    if (tab === "news") {
      document.getElementById("filters").style.display = "";
      document.getElementById("cards").style.display = "";
      document.getElementById("research-section").style.display = "none";
      document.getElementById("subtitle").textContent =
        scrapedData.source_count + " sources \u00b7 " + allItems.length + " articles \u00b7 live";
    } else {
      document.getElementById("filters").style.display = "none";
      document.getElementById("cards").style.display = "none";
      document.getElementById("research-section").style.display = "";
      renderResearchCards();
      document.getElementById("subtitle").textContent =
        "45+ research sources \u00b7 " + researchData.length + " papers";
    }
  });

  function buildFilters() {
    var types = [];
    var seen = {};
    allItems.forEach(function (item) {
      if (!seen[item.type]) {
        seen[item.type] = true;
        types.push(item.type);
      }
    });
    types.sort();

    var filtersEl = document.getElementById("filters");
    filtersEl.innerHTML = "";
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
        applyFilter(activeFilter);
      });
      filtersEl.appendChild(btn);
    });
  }

  function renderCards() {
    var cardsEl = document.getElementById("cards");
    cardsEl.innerHTML = "";

    allItems.forEach(function (item, idx) {
      var colorIdx = idx % COLORS.length;
      var cardColor = COLOR_MAP[COLORS[colorIdx]];
      var card = document.createElement("div");
      card.className = "card";
      card.dataset.type = item.type;
      card.style.setProperty("--card-color", cardColor);
      card.style.animationDelay = idx * 30 + "ms";

      var liveBadge = item.via === "rss"
        ? '<span class="live-badge"><span class="live-dot"></span>LIVE</span>'
        : "";

      var desc = item.description
        ? '<p class="description">' + escapeHtml(item.description) + "</p>"
        : "";

      var timeStr = item.published || scrapedData.generated_at || "";
      card.innerHTML =
        '<span class="type-badge">' + escapeHtml(item.type.toUpperCase()) + "</span>" +
        liveBadge +
        '<span class="source-tag">' + escapeHtml(item.source) + "</span>" +
        "<h3>" + escapeHtml(item.title) + "</h3>" +
        desc +
        '<div class="meta">' +
        '<a href="' + escapeHtml(item.url) + '" target="_blank" rel="noopener">Read more \u2192</a>' +
        "<time>" + relativeTime(timeStr) + "</time>" +
        "</div>";
      cardsEl.appendChild(card);
    });
  }

  function renderResearchCards() {
    var grid = document.getElementById("research-grid");
    if (!grid) return;
    grid.innerHTML = "";

    // Build category filters
    var categories = {};
    researchData.forEach(function (p) {
      var cat = p.category || "unknown";
      categories[cat] = (categories[cat] || 0) + 1;
    });
    var filtersEl = document.getElementById("research-filters");
    filtersEl.innerHTML = "";
    var catFilter = null;

    Object.keys(categories).sort().forEach(function (cat) {
      var btn = document.createElement("button");
      btn.className = "filter-pill";
      btn.textContent = cat.toUpperCase() + " (" + categories[cat] + ")";
      btn.addEventListener("click", function () {
        if (catFilter === cat) {
          catFilter = null;
          btn.classList.remove("active");
        } else {
          catFilter = cat;
          filtersEl.querySelectorAll(".filter-pill").forEach(function (b) { b.classList.remove("active"); });
          btn.classList.add("active");
        }
        grid.querySelectorAll(".research-card").forEach(function (card) {
          card.style.display = (!catFilter || card.dataset.category === catFilter) ? "" : "none";
        });
      });
      filtersEl.appendChild(btn);
    });

    researchData.forEach(function (paper, idx) {
      var colorIdx = idx % COLORS.length;
      var cardColor = COLOR_MAP[COLORS[colorIdx]];
      var card = document.createElement("div");
      card.className = "research-card";
      card.dataset.category = paper.category || "unknown";
      card.style.setProperty("--card-color", cardColor);

      var oaBadge = paper.pdf_url
        ? '<span class="oa-badge">OA PDF</span>'
        : "";
      var venue = paper.venue ? '<span class="venue-tag">' + escapeHtml(paper.venue) + "</span>" : "";
      var citations = paper.citations > 0
        ? '<span class="citation-count">' + paper.citations + " citations</span>"
        : "";
      var authors = (paper.authors || []).slice(0, 3).join(", ");
      if ((paper.authors || []).length > 3) authors += " et al.";

      var abstract = paper.abstract || "";
      var hasAbstract = abstract.length > 50;
      var abstractBlock = hasAbstract
        ? '<details class="abstract-toggle"><summary>Abstract</summary><p>' + escapeHtml(abstract) + "</p></details>"
        : "";

      var aiSummary = paper.ai_summary
        ? '<div class="ai-summary"><strong>AI Summary:</strong> ' + escapeHtml(paper.ai_summary) + "</div>"
        : "";

      var pdfLink = paper.pdf_url
        ? '<a href="' + escapeHtml(paper.pdf_url) + '" target="_blank" rel="noopener" class="pdf-link">PDF</a>'
        : "";

      var pubDate = paper.published || "";

      card.innerHTML =
        '<span class="type-badge">' + escapeHtml((paper.category || "paper").toUpperCase()) + "</span>" +
        oaBadge +
        venue +
        "<h3>" + escapeHtml(paper.title) + "</h3>" +
        '<p class="authors">' + escapeHtml(authors) + "</p>" +
        abstractBlock +
        aiSummary +
        '<div class="meta">' +
        pdfLink +
        citations +
        "<time>" + pubDate + "</time>" +
        "</div>";
      grid.appendChild(card);
    });
  }

  function mergeAndRender() {
    var seen = {};
    allItems = [];
    scrapedData.items.forEach(function (item) {
      if (!seen[item.url]) {
        seen[item.url] = true;
        allItems.push(item);
      }
    });
    liveItems.forEach(function (item) {
      if (!seen[item.url]) {
        seen[item.url] = true;
        allItems.push(item);
      }
    });
    buildFilters();
    renderCards();
    var subtitleEl = document.getElementById("subtitle");
    if (subtitleEl) {
      var rssCount = liveItems.length;
      var totalCount = allItems.length;
      subtitleEl.textContent = scrapedData.source_count + " sources \u00b7 " + totalCount + " articles \u00b7 live";
    }
  }

  function applyFilter(filter) {
    document.querySelectorAll(".card").forEach(function (card) {
      if (!filter || card.dataset.type === filter) {
        card.style.display = "";
      } else {
        card.style.display = "none";
      }
    });
  }

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

  function escapeHtml(str) {
    var div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  function parseRSSFeed(xml, sourceName) {
    var parser = new DOMParser();
    var doc = parser.parseFromString(xml, "text/xml");
    var items = [];
    var entries = doc.querySelectorAll("entry, item");
    entries.forEach(function (entry) {
      var titleEl = entry.querySelector("title");
      var linkEl = entry.querySelector("link");
      var pubEl = entry.querySelector("published, updated, pubDate");
      if (!titleEl || !linkEl) return;
      var title = titleEl.textContent.trim();
      var url = linkEl.getAttribute("href") || linkEl.textContent.trim();
      var published = pubEl ? pubEl.textContent.trim() : "";
      if (title && url) {
        items.push({ title: title, url: url, published: published });
      }
    });
    return items.slice(0, 5);
  }

  async function fetchWithProxy(url) {
    for (var i = 0; i < CORS_PROXIES.length; i++) {
      try {
        var resp = await fetch(CORS_PROXIES[i] + encodeURIComponent(url));
        if (resp.ok) return await resp.text();
      } catch (e) {}
    }
    return null;
  }

  async function pollRSS() {
    var newItems = [];
    var entries = Object.entries(rssMap);
    var chunks = [];
    for (var i = 0; i < entries.length; i += 10) {
      chunks.push(entries.slice(i, i + 10));
    }
    for (var c = 0; c < chunks.length; c++) {
      var batch = chunks[c];
      var results = await Promise.allSettled(
        batch.map(async function (pair) {
          var name = pair[0], feedUrl = pair[1];
          if (!feedUrl) return [];
          var xml = await fetchWithProxy(feedUrl);
          if (!xml) return [];
          return parseRSSFeed(xml, name).map(function (item) {
            return {
              source: name,
              type: getTypeForSource(name),
              title: item.title,
              url: item.url,
              description: "",
              via: "rss",
              published: item.published,
            };
          });
        })
      );
      results.forEach(function (r) {
        if (r.status === "fulfilled") newItems.push.apply(newItems, r.value);
      });
    }
    if (newItems.length > 0) {
      liveItems = newItems;
      mergeAndRender();
    }
  }

  function getTypeForSource(name) {
    for (var i = 0; i < (window.__urlsData || []).length; i++) {
      if (window.__urlsData[i].name === name) return window.__urlsData[i].type;
    }
    var rssTypeMap = {
      "TechCrunch": "startups", "The Verge": "news", "WIRED": "news",
      "Ars Technica": "news", "VentureBeat": "ai", "Hacker News": "community",
      "9to5Mac": "apple", "9to5Google": "google", "Android Authority": "android",
      "MIT Technology Review": "research", "Futurism": "news", "The Register": "news",
      "NYT Technology": "news", "DEV.to": "blog", "Dev.to AI": "ai",
      "HackerNoon": "blog", "Smashing Magazine": "blog", "CSS-Tricks": "blog",
      "SitePoint": "blog", "freeCodeCamp News": "blog", "The New Stack": "enterprise",
      "InfoQ": "research", "DZone": "enterprise", "Habr": "blog",
      "arXiv CS": "research", "Nature Technology": "research",
    };
    return rssTypeMap[name] || "news";
  }

  mergeAndRender();
  pollRSS();
  setInterval(pollRSS, POLL_INTERVAL);
})();
