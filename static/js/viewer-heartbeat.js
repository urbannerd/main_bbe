(() => {
  const stream = document.body.dataset.stream;
  if (!stream) return;

  let viewerId = localStorage.getItem("viewer_id");
  if (!viewerId) {
    viewerId = crypto.randomUUID();
    localStorage.setItem("viewer_id", viewerId);
  }

  async function sendHeartbeat() {
    try {
      await fetch(`/viewer/heartbeat?stream=${stream}&id=${viewerId}`, {
        method: "POST",
        keepalive: true
      });
    } catch {}
  }

  sendHeartbeat();
  setInterval(sendHeartbeat, 15000);
})();
