// dash.js - Updated with smoother UI interactions

// Load saved profile pic and user details
window.addEventListener("DOMContentLoaded", () => {
  const savedPfp = localStorage.getItem("pfp");
  if (savedPfp) {
    document.getElementById("profilePic").src = savedPfp;
  }

  const savedUsername = localStorage.getItem("userName");
  if (savedUsername) {
    document.getElementById("userName").innerHTML = `Welcome, <span style="color:#ff8500">${savedUsername}</span>`;
  }

  const savedEmail = localStorage.getItem("userEmail");
  if (savedEmail) {
    document.getElementById("userEmail").innerText = savedEmail;
  }

  updateXPBar();
  loadUnlockedBadges();
});

// XP Progress
function updateXPBar() {
  const xp = parseInt(localStorage.getItem("xp")) || 0;
  const maxXP = parseInt(localStorage.getItem("maxXP")) || 500;
  const percent = Math.min(Math.round((xp / maxXP) * 100), 100);
  const xpFill = document.getElementById("xpFill");
  xpFill.style.width = percent + "%";
  xpFill.innerText = `${xp} / ${maxXP} XP`;
}

// Camera Functions
function startCamera() {
  const video = document.getElementById("camera");
  const snapBtn = document.getElementById("snapBtn");
  video.style.display = "block";
  snapBtn.style.display = "inline";

  navigator.mediaDevices.getUserMedia({ video: true })
    .then(stream => {
      video.srcObject = stream;
    })
    .catch(err => {
      console.error("Camera access failed:", err);
      alert("Camera not accessible.");
    });
}

function capturePhoto() {
  const video = document.getElementById("camera");
  const canvas = document.createElement("canvas");
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  const ctx = canvas.getContext("2d");
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

  const dataURL = canvas.toDataURL("image/png");
  document.getElementById("profilePic").src = dataURL;
  localStorage.setItem("pfp", dataURL);

  video.srcObject.getTracks().forEach(track => track.stop());
  video.style.display = "none";
  document.getElementById("snapBtn").style.display = "none";
}

// Profile Picture File Upload
const pfpInput = document.getElementById("pfpInput");
pfpInput.addEventListener("change", () => {
  const file = pfpInput.files[0];
  if (file) {
    const reader = new FileReader();
    reader.onload = function (e) {
      const dataURL = e.target.result;
      document.getElementById("profilePic").src = dataURL;
      localStorage.setItem("pfp", dataURL);
    };
    reader.readAsDataURL(file);
  }
});

// Achievements
const achievements = [
  { id: "firstEdit", name: "First Edit", requiredXP: 10 },
  { id: "xp100", name: "100 XP Club", requiredXP: 100 },
  { id: "xp250", name: "Quarter King", requiredXP: 250 },
  { id: "xp500", name: "Halfway Hero", requiredXP: 500 },
];

function checkAchievements(currentXP) {
  achievements.forEach(a => {
    if (currentXP >= a.requiredXP && !localStorage.getItem("achv_" + a.id)) {
      unlockAchievement(a);
    }
  });
}

function unlockAchievement(achv) {
  localStorage.setItem("achv_" + achv.id, "true");
  alert("🎉 Unlocked: " + achv.name);
  loadUnlockedBadges();
}

function loadUnlockedBadges() {
  document.querySelectorAll(".badge").forEach(badge => {
    const id = badge.dataset.id;
    if (id && localStorage.getItem("achv_" + id)) {
      badge.classList.add("unlocked");
    }
  });
}

// Badge hover interaction
const badgeGrid = document.getElementById("badgeGrid");
const detailIcon = document.getElementById("detailIcon");
const detailTitle = document.getElementById("detailTitle");
const detailDesc = document.getElementById("detailDesc");
const detailProgress = document.getElementById("detailProgress");

badgeGrid.addEventListener("mouseover", (e) => {
  const badge = e.target.closest(".badge");
  if (badge) {
    const icon = badge.dataset.icon || "fa-medal";
    detailIcon.innerHTML = `<i class="fa-solid ${icon}"></i>`;
    detailTitle.innerText = badge.dataset.title;
    detailDesc.innerText = badge.dataset.desc;
    detailProgress.innerText = badge.dataset.progress;
  }
});
