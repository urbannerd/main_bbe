document.addEventListener("DOMContentLoaded", () => {
  const year = document.getElementById("y");
  if (year) year.textContent = new Date().getFullYear();

  const anchorLinks = document.querySelectorAll('a[href^="#"]');
  anchorLinks.forEach((link) => {
    link.addEventListener("click", (event) => {
      const href = link.getAttribute("href");
      if (!href || href === "#") return;

      const target = document.querySelector(href);
      if (!target) return;

      event.preventDefault();
      target.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    });
  });

  initHomePreview();
  initImpulseSnapshot();
});

function initHomePreview() {
  if (!window.BBE_CONFIG?.endpoints?.homePreview) return;
  loadHomePreview();
  setInterval(loadHomePreview, window.BBE_CONFIG.refreshMs || 10000);
}

function initImpulseSnapshot() {
  if (!window.BBE_CONFIG?.endpoints?.impulseSnapshot) return;
  loadImpulseSnapshot();
  setInterval(loadImpulseSnapshot, window.BBE_CONFIG.refreshMs || 10000);
}

async function loadHomePreview() {
  try {
    const response = await fetch(window.BBE_CONFIG.endpoints.homePreview, {
      headers: { Accept: "application/json" }
    });

    if (!response.ok) throw new Error(`HTTP ${response.status}`);

    const data = await response.json();
    renderSpy(data.spy || {});
  } catch (error) {
    console.error("Failed to load SPY preview:", error);
  }
}

async function loadImpulseSnapshot() {
  try {
    const response = await fetch(window.BBE_CONFIG.endpoints.impulseSnapshot, {
      headers: { Accept: "application/json" }
    });

    if (!response.ok) throw new Error(`HTTP ${response.status}`);

    const data = await response.json();
    renderImpulseSnapshot(data.rows || []);
  } catch (error) {
    console.error("Failed to load impulse snapshot:", error);
    const status = document.getElementById("impulse-list-status");
    if (status) status.textContent = "unavailable";
  }
}

function renderSpy(spy) {
  const title = document.getElementById("spy-live-title");
  const desc = document.getElementById("spy-live-desc");
  const spark = document.getElementById("spy-live-spark");

  const price = safe(spy.price, "--");
  const rawChange = spy.changePercent;
  const change =
    rawChange === undefined || rawChange === null || rawChange === "--" || rawChange === ""
      ? ""
      : String(rawChange);

  if (title) {
    title.textContent = change ? `SPY ${price} · ${change}` : `SPY ${price}`;
  }



  if (spark) {
    spark.style.setProperty("--spark-strength", Number(spy.strength || 50));
  }
}

function renderImpulseSnapshot(rows) {
  const marketOpen = isUsMarketOpen();

  const title = document.getElementById("impulse-live-title");
  const desc = document.getElementById("impulse-live-desc");
  const spark = document.getElementById("impulse-live-spark");
  const status = document.getElementById("impulse-list-status");

  if (title) {
    title.textContent = marketOpen ? "Volatility Movers" : "Tracked Names";
  }

  if (desc) {
    desc.textContent = marketOpen
      ? "Find the loud names when the tape gets active."
      : "Real prices for names we watch into the close and after hours.";
  }

  if (spark) {
    spark.style.setProperty("--spark-strength", marketOpen ? 76 : 32);
  }

  if (status) {
    status.textContent = marketOpen ? "live snapshot" : "after hours";
  }

  const closedMeta = {
    TSLA: { label: "watching", tag: "EV" },
    NVDA: { label: "watching", tag: "AI" },
    AAPL: { label: "watching", tag: "Mega Cap" },
  };

  for (let i = 0; i < 3; i++) {
    const row = rows[i];
    const symbolEl = document.getElementById(`impulse-row-${i + 1}-symbol`);
    const changeEl = document.getElementById(`impulse-row-${i + 1}-change`);
    const tagEl = document.getElementById(`impulse-row-${i + 1}-tag`);

    if (!symbolEl || !changeEl || !tagEl) continue;

    if (!row) {
      symbolEl.innerHTML = `<span class="sym">--</span> <span style="color:var(--muted2)">— --</span>`;
      changeEl.textContent = "";
      tagEl.textContent = "";
      continue;
    }

    symbolEl.innerHTML = `<span class="sym">${escapeHtml(row.symbol)}</span> <span style="color:var(--muted2)">— ${escapeHtml(row.price)}</span>`;

    if (marketOpen) {
      changeEl.textContent = row.openLabel || "active";
      tagEl.textContent = row.openTag || "Live";
      changeEl.classList.remove("down");
      changeEl.style.color = "var(--muted2)";
    } else {
      const meta = closedMeta[row.symbol] || { label: "watching", tag: "Tracked" };
      changeEl.textContent = meta.label;
      tagEl.textContent = meta.tag;
      changeEl.classList.remove("down");
      changeEl.style.color = "var(--muted2)";
    }
  }
}

function isUsMarketOpen() {
  const now = new Date();

  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: "America/New_York",
    weekday: "short",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false
  }).formatToParts(now);

  const weekday = parts.find(p => p.type === "weekday")?.value;
  const hour = Number(parts.find(p => p.type === "hour")?.value ?? "0");
  const minute = Number(parts.find(p => p.type === "minute")?.value ?? "0");

  const totalMinutes = hour * 60 + minute;
  const isWeekday = ["Mon", "Tue", "Wed", "Thu", "Fri"].includes(weekday);
  const marketOpen = 9 * 60 + 30;
  const marketClose = 16 * 60;

  return isWeekday && totalMinutes >= marketOpen && totalMinutes < marketClose;
}

function safe(value, fallback) {
  return value === undefined || value === null || value === "" ? fallback : String(value);
}

function escapeHtml(str) {
  return String(str)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}