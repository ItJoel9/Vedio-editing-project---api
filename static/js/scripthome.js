let reelList = [];
let currentReelIndex = 0;

// Open the reel in modal like Insta
function openReel(videoSrc, index) {
  const modal = document.getElementById("reelModal");
  const modalVideo = document.getElementById("modalVideo");

  modal.style.display = "flex";
  modalVideo.src = videoSrc;
  modalVideo.play();
  currentReelIndex = index;
}

// Close modal and stop video
function closeReel() {
  const modal = document.getElementById("reelModal");
  const modalVideo = document.getElementById("modalVideo");

  modal.style.display = "none";
  modalVideo.pause();
  modalVideo.src = "";
}

// Show reel by index
function showReelByIndex(index) {
  if (index >= 0 && index < reelList.length) {
    openReel(reelList[index], index);
  }
}

// Detect swipe direction (touch-based)
function addSwipeDetection(element) {
  let startY = 0;

  element.addEventListener("touchstart", (e) => {
    startY = e.touches[0].clientY;
  });

  element.addEventListener("touchend", (e) => {
    const endY = e.changedTouches[0].clientY;
    const diff = startY - endY;

    if (Math.abs(diff) > 50) {
      if (diff > 0) {
        showReelByIndex(currentReelIndex + 1); // swipe up
      } else {
        showReelByIndex(currentReelIndex - 1); // swipe down
      }
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  const modal = document.getElementById("reelModal");
  const modalVideo = document.getElementById("modalVideo");
  const closeBtn = document.querySelector(".close-modal");

  // Store all reel video sources
  const reels = document.querySelectorAll(".reel");
  reels.forEach((reel, index) => {
    const video = reel.querySelector("video");
    const videoSrc = video.querySelector("source").src;
    reelList.push(videoSrc);

    // Click reel to open modal
    reel.addEventListener("click", () => {
      openReel(videoSrc, index);
    });

    // Controls container
    let controls = reel.querySelector(".controls");
    if (!controls) {
      controls = document.createElement("div");
      controls.classList.add("controls");
      reel.appendChild(controls);
    }

    // Fullscreen Button only
    const fullScreenBtn = document.createElement("button");
    fullScreenBtn.classList.add("fullscreen-button");
    fullScreenBtn.innerHTML = "⛶";
    controls.appendChild(fullScreenBtn);

    fullScreenBtn.addEventListener("click", (event) => {
      event.stopPropagation();
      openReel(videoSrc, index);
    });
  });

  // Swipe detection on modal
  addSwipeDetection(modal);

  // Close modal events
  closeBtn.addEventListener("click", closeReel);
  modal.addEventListener("click", (e) => {
    if (e.target === modal) closeReel();
  });

  // Keyboard navigation
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeReel();
    if (e.key === "ArrowDown") showReelByIndex(currentReelIndex + 1);
    if (e.key === "ArrowUp") showReelByIndex(currentReelIndex - 1);
  });
});
function expandSidebar() {
  document.body.classList.add('sidebar-expanded');
}
function collapseSidebar() {
  document.body.classList.remove('sidebar-expanded');
}