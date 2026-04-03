(function () {
  const params = new URLSearchParams(window.location.search);
  if (params.get("admin") !== "1") return;

  const stream = document.body.dataset.stream;
  if (!stream) return;

  const viewerBox = document.getElementById("viewerCount");
  const viewerNum = document.getElementById("viewerNumber");
  if (!viewerBox || !viewerNum) return;

  viewerBox.style.display = "inline-flex";

  async function updateViewerCount() {
    try {
      const res = await fetch(`/viewer/count?stream=${stream}`, {
        cache: "no-store"
      });
      const data = await res.json();
      const count = data.count ?? 0;

      viewerNum.textContent = count;
      viewerBox.style.display = count > 0 ? "inline-flex" : "none";
    } catch (e) {
      console.error("viewer count error", e);
    }
  }

  updateViewerCount();
  setInterval(updateViewerCount, 5000);
})();
