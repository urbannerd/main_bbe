/* ================= MARKET LOGIC ================= */

const video = document.getElementById("player");
const closed = document.getElementById("closed");
const liveBadge = document.getElementById("liveBadge");

let lastState = null;

function getET() {
  return new Date(
    new Date().toLocaleString("en-US", { timeZone: "America/New_York" })
  );
}

function isMarketOpen() {
  const et = getET();
  const day = et.getDay();
  if (day === 0 || day === 6) return false;

  const minutes = et.getHours() * 60 + et.getMinutes();
  return minutes >= 570 && minutes < 960; // 9:30–16:00 ET
}

function updateMarketState() {
  if (!video || !closed || !liveBadge) return;

  const open = isMarketOpen();
  const state = open ? "open" : "closed";

  if (state === lastState) return;
  lastState = state;

  if (open) {
    closed.style.display = "none";
    liveBadge.style.display = "inline-block";
    video.style.display = "block";
    video.muted = true;
    video.play().catch(() => {});
  } else {
    liveBadge.style.display = "none";
    closed.style.display = "flex";
    video.pause();
    video.style.display = "none";
  }
}

// Initial run
updateMarketState();

// Re-check every minute
setInterval(updateMarketState, 60000);
