function openModal(url) {
  document.getElementById('tutorialVideo').src = url;
  document.getElementById('modal').style.display = 'flex';
}

function closeModal() {
  const modal = document.getElementById('modal');
  modal.style.display = 'none';
  document.getElementById('tutorialVideo').src = '';
}

function tryTransition(type) {
    const editorSection = document.getElementById("editorSection");
    const editorTitle = document.getElementById("transitionTitle");
    const editorContainer = document.getElementById("videoEditor");
  
    editorTitle.textContent = type.charAt(0).toUpperCase() + type.slice(1) + " Transition";
    editorSection.style.display = "block";
  
    editorContainer.innerHTML = `
      <video id="previewVideo" width="100%" controls autoplay>
        <source src="sample.mp4" type="video/mp4">
        Your browser does not support the video tag.
      </video>
    `;
  
    setTimeout(() => {
      document.getElementById("previewVideo").classList.add(type);
    }, 100);
  }

  function simplifyTitle(original) {
    if (original.toLowerCase().includes("glitch")) return "Glitch Transition";
    if (original.toLowerCase().includes("zoom")) return "Zoom Transition";
    if (original.toLowerCase().includes("swipe")) return "Swipe Transition";
    if (original.toLowerCase().includes("shake")) return "Shake Effect";
    if (original.toLowerCase().includes("slide")) return "Slide Transition";
    if (original.toLowerCase().includes("spin")) return "Spin Zoom";
    return original; // fallback
  }
  const rawTitle = item.snippet.title;
  const title = simplifyTitle(rawTitle);
    