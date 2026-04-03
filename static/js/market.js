/* ================= MARKET HOURS (SCANNER OVERLAY) ================= */

(() => {
  const screen = document.getElementById("marketClosedScreen");
  const reasonEl = document.getElementById("marketClosedReason");
  const appShell = document.getElementById("appShell");
  const page = document.querySelector("main.page"); // your content

  let lastState = null;

  function getET() {
    return new Date(new Date().toLocaleString("en-US", { timeZone: "America/New_York" }));
  }

  function ymd(d) {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return `${y}-${m}-${day}`;
  }

  function addDays(d, n) {
    const x = new Date(d);
    x.setDate(x.getDate() + n);
    return x;
  }

  function nthWeekdayOfMonth(year, monthIndex, weekday, n) {
    const first = new Date(year, monthIndex, 1);
    const firstW = first.getDay();
    const delta = (weekday - firstW + 7) % 7;
    const day = 1 + delta + (n - 1) * 7;
    return new Date(year, monthIndex, day);
  }

  function lastWeekdayOfMonth(year, monthIndex, weekday) {
    const last = new Date(year, monthIndex + 1, 0);
    const lastW = last.getDay();
    const delta = (lastW - weekday + 7) % 7;
    return new Date(year, monthIndex, last.getDate() - delta);
  }

  // Meeus/Jones/Butcher Gregorian Easter, then Good Friday = Easter - 2
  function easterDate(year) {
    const a = year % 19;
    const b = Math.floor(year / 100);
    const c = year % 100;
    const d = Math.floor(b / 4);
    const e = b % 4;
    const f = Math.floor((b + 8) / 25);
    const g = Math.floor((b - f + 1) / 3);
    const h = (19 * a + b - d - g + 15) % 30;
    const i = Math.floor(c / 4);
    const k = c % 4;
    const l = (32 + 2 * e + 2 * i - h - k) % 7;
    const m = Math.floor((a + 11 * h + 22 * l) / 451);
    const month = Math.floor((h + l - 7 * m + 114) / 31);
    const day = ((h + l - 7 * m + 114) % 31) + 1;
    return new Date(year, month - 1, day);
  }

  function observedFixedHoliday(year, monthIndex, dayOfMonth) {
    const d = new Date(year, monthIndex, dayOfMonth);
    const wd = d.getDay();
    if (wd === 6) return addDays(d, -1); // Sat -> Fri
    if (wd === 0) return addDays(d, 1);  // Sun -> Mon
    return d;
  }

  function usMarketHolidaysSet(year) {
    const hol = [];

    // Fixed (observed)
    hol.push(observedFixedHoliday(year, 0, 1));    // New Year's Day
    hol.push(observedFixedHoliday(year, 5, 19));   // Juneteenth
    hol.push(observedFixedHoliday(year, 6, 4));    // Independence Day
    hol.push(observedFixedHoliday(year, 11, 25));  // Christmas

    // Floating
    hol.push(nthWeekdayOfMonth(year, 0, 1, 3));    // MLK Day: 3rd Monday Jan
    hol.push(nthWeekdayOfMonth(year, 1, 1, 3));    // Presidents Day: 3rd Monday Feb
    hol.push(lastWeekdayOfMonth(year, 4, 1));      // Memorial Day: last Monday May
    hol.push(nthWeekdayOfMonth(year, 8, 1, 1));    // Labor Day: 1st Monday Sep
    hol.push(nthWeekdayOfMonth(year, 10, 4, 4));   // Thanksgiving: 4th Thursday Nov

    // Good Friday
    hol.push(addDays(easterDate(year), -2));

    return new Set(hol.map(ymd));
  }

  function isMarketOpen() {
    const et = getET();
    const day = et.getDay();
    if (day === 0 || day === 6) return false;

    const holidays = usMarketHolidaysSet(et.getFullYear());
    if (holidays.has(ymd(et))) return false;

    const minutes = et.getHours() * 60 + et.getMinutes();
    return minutes >= 570 && minutes < 960; // 9:30–16:00 ET
  }

  function updateMarketState() {
    if (!screen || !appShell || !page) return;

    const open = isMarketOpen();
    const state = open ? "open" : "closed";
    if (state === lastState) return;
    lastState = state;

    if (open) {
      screen.style.display = "none";
      appShell.style.display = "";
      page.style.display = "";
    } else {
      // SHOW CLOSED OVERLAY
      screen.style.display = "flex";
      appShell.style.display = "none";
      page.style.display = "none";

      // you asked to remove “After 4:00 ET” (and any reason text)
      if (reasonEl) {
        reasonEl.textContent = "";
        reasonEl.style.display = "none";
      }
    }
  }

  updateMarketState();
  setInterval(updateMarketState, 60_000);
})();
