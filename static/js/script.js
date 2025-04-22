// Element references
const mediaInput = document.getElementById('mediaInput');
const videoPreview = document.getElementById('videoPreview');
const mediaLibrary = document.getElementById('mediaLibrary');
const videoTrack = document.getElementById('videoTrack');
const trimStartInput = document.getElementById('trimStart');
const trimEndInput = document.getElementById('trimEnd');
const applyTrimBtn = document.getElementById('applyTrimBtn');
const cutButton = document.getElementById('cutButton');
const playPauseBtn = document.getElementById('playPauseBtn');
const detailsPanel = document.getElementById('details');
const exportButton = document.getElementById('exportButton');
const playhead = document.getElementById('playhead');

// App state
let clips = [];
let currentClip = null;

// File import
mediaInput.addEventListener('change', (e) => {
    const files = Array.from(e.target.files);
    files.forEach(file => {
        const url = URL.createObjectURL(file);
        const clip = {
            id: Date.now() + Math.random(),
            name: file.name,
            url,
            type: file.type,
            start: 0,
            end: null,
            timelineElement: null
        };
        clips.push(clip);
        addToLibrary(clip);
        addToTimeline(clip);
    });
});

// Add to media library
function addToLibrary(clip) {
    const div = document.createElement('div');
    div.textContent = clip.name;
    div.style.cursor = 'pointer';
    div.onclick = () => loadClip(clip);
    mediaLibrary.appendChild(div);
}

// Add to timeline
function addToTimeline(clip) {
    const div = document.createElement('div');
    div.className = 'clip-thumb';
    div.textContent = clip.name.split('.')[0];
    Object.assign(div.style, {
        background: '#ff8500',
        padding: '5px',
        borderRadius: '5px',
        cursor: 'pointer',
        minWidth: '100px',
        textAlign: 'center',
        marginRight: '10px'
    });
    div.title = "Click to select";

    div.onclick = () => {
        document.querySelectorAll('.clip-thumb').forEach(el => el.style.outline = 'none');
        div.style.outline = '2px solid white';
        loadClip(clip);
    };

    videoTrack.appendChild(div);
    clip.timelineElement = div;
}

// Load clip into preview
function loadClip(clip) {
    currentClip = clip;
    videoPreview.src = clip.url;
    videoPreview.currentTime = clip.start || 0;
    trimStartInput.value = clip.start || 0;
    trimEndInput.value = clip.end ?? videoPreview.duration;
    videoPreview.play();
    playPauseBtn.textContent = "⏸ Pause";
    updateDetails(clip);
}

// Update right sidebar info panel
function updateDetails(clip) {
    detailsPanel.innerHTML = `
        <strong>${clip.name}</strong><br>
        Start: ${clip.start.toFixed(2)}s<br>
        End: ${(clip.end ?? "Full")}<br>
        <button onclick="deleteClip('${clip.id}')">🗑 Delete Clip</button>
    `;
}

// Trim current clip
applyTrimBtn.onclick = () => {
    if (!currentClip) return;

    const start = parseFloat(trimStartInput.value);
    const end = parseFloat(trimEndInput.value);
    const duration = videoPreview.duration;

    if (isNaN(start) || isNaN(end) || start < 0 || end <= start || end > duration) {
        alert("Invalid trim values");
        return;
    }

    currentClip.start = start;
    currentClip.end = end;
    updateDetails(currentClip);
};

// Cut at current time
cutButton.onclick = () => {
    if (!currentClip) return;

    const time = videoPreview.currentTime;
    const { start, end } = currentClip;

    if (time <= start || time >= (end ?? videoPreview.duration)) return;

    const index = clips.indexOf(currentClip);
    if (index === -1) return;

    // Create two new split clips
    const firstPart = { ...currentClip, end: time, id: Date.now() + Math.random() };
    const secondPart = { ...currentClip, start: time, id: Date.now() + Math.random() };

    // Replace the original
    clips.splice(index, 1, firstPart, secondPart);

    currentClip.timelineElement?.remove();
    addToTimeline(firstPart);
    addToTimeline(secondPart);
    loadClip(firstPart);
};

// Play / Pause toggle
playPauseBtn.onclick = () => {
    if (videoPreview.paused) {
        videoPreview.play();
        playPauseBtn.textContent = "⏸ Pause";
    } else {
        videoPreview.pause();
        playPauseBtn.textContent = "▶ Play";
    }
};

// Update playhead + auto-pause at trim end
videoPreview.ontimeupdate = () => {
    const currentTime = videoPreview.currentTime;
    const duration = videoPreview.duration || 1;
    const percent = (currentTime / duration) * 100;
    playhead.style.left = percent + '%';

    if (currentClip?.end && currentTime >= currentClip.end) {
        videoPreview.pause();
        playPauseBtn.textContent = "▶ Play";
    }
};

// Delete clip
function deleteClip(id) {
    const index = clips.findIndex(c => c.id == id);
    if (index === -1) return;

    const clip = clips[index];
    clip.timelineElement?.remove();
    clips.splice(index, 1);
    currentClip = null;
    videoPreview.src = '';
    playPauseBtn.textContent = "▶ Play";
    detailsPanel.innerHTML = "Clip deleted.";
}

// Simulate export
exportButton.onclick = () => {
    if (!currentClip) {
        alert("Select a clip first.");
        return;
    }

    const start = currentClip.start.toFixed(2);
    const end = (currentClip.end ?? videoPreview.duration).toFixed(2);
    alert(`Simulating export from ${start}s to ${end}s of ${currentClip.name}`);
    // Real export? Use ffmpeg.wasm or server-side Flask + moviepy later
};
