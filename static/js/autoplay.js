    (() => {
      const video = document.getElementById("player");
      if (!video) return;
    
      function tryPlay() {
        video.muted = true;
        video.setAttribute("muted", "");
        const p = video.play();
        if (p && typeof p.catch === "function") {
          p.catch(() => {});
        }
      }
    
      // í ½í´¹ Autoplay attempts
      tryPlay();
      video.addEventListener("loadedmetadata", tryPlay);
      video.addEventListener("canplay", tryPlay);
      video.addEventListener("canplaythrough", tryPlay);
    
      // í ½í´¹ Enable controls ONLY after playback starts
      video.addEventListener("playing", () => {
        video.controls = true;
      });
    
      // í ½í´¹ Mobile Safari fallback
      document.addEventListener("click", tryPlay, { once: true });
    })();
