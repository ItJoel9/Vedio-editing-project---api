<img src="https://github.com/user-attachments/assets/6401caed-41b8-4537-89d5-2fad528abb39" alt="Vdio Banner" style="width:100%; max-height:100px; object-fit:cover;">


# Vdio - Creative Video Editing Platform

**Vdio** is a full-stack video editing, learning, and challenge platform built with Flask, MongoDB, and JavaScript. It combines creative tools, educational tutorials, and interactive components for creators, editors, and students.

---

## Project Structure

```
vdio/
├── app.py                            # Flask backend with routes and logic
├── client_secret.json               # Google OAuth or API client (if used)
├── .env                             # Environment variables
├── static/
│   ├── css/                         # All custom CSS
│   ├── js/                          # JavaScript logic (UI, search, etc.)
│   ├── media/                       # Backgrounds, logos, assets
│   └── uploads/                     # Uploaded files (audio/video)
├── templates/                       # Flask-rendered HTML (Jinja2)
│   ├── transitions_page.html
│   ├── music_page.html
│   ├── challenges.html
│   ├── dashboard.html
│   └── login.html
├── converted/                       # Converted video files
├── exp/                             # XP system (future)
├── editor test/                     # Editor test files (CapCut-style)
├── flask_session/                   # Session cache
├── temp_sessions/                   # Active temp sessions
├── uploads/                         # Global upload temp folder
├── requirements.txt
└── README.md
```

---

## Features Overview

### General

* User login system with session persistence
* Sidebar UI navigation with hover expand
* Global search bar with enter-key navigation
* Smart "Tip of the Day" system

### Music System

* Displays top 10 songs per genre
* Spotify Embed Player integration
* Voting logic stored per track and user
* Genre filter buttons
* Recommendation system placeholder

### Transition Tutorials

* Fetched from YouTube playlist via API
* Tracks watched videos using MongoDB
* Filtered by effect (zoom, glitch, etc.)
* Mark as watched through `/api/mark_transition`

### Video & Audio Tools

* **Video Converter**

  * FFmpeg-based backend
  * Converts between MP4, AVI, MOV, MKV
* **Audio Trimmer**

  * Uses Wavesurfer.js
  * Drag-and-trim interface
  * Outputs in MP3 or WAV

### Weekly Challenges

* Upload edit files (videos)
* Email auto-filled from session
* MongoDB structure: `title`, `user`, `filename`, `status`
* File stored in `static/uploads/challenges`
* Toast feedback on submission

---

## ML Integration and Plans

* Voting system (likes/dislikes on music) stored in `track_votes`
* Watched tutorials saved in `tutorial_progress`
* Planned models:

  * Style clustering
  * Emotion prediction from music title/genre
  * Tutorial recommendation based on past completions

### Possible ML Stack

* Scikit-learn
* Pandas/Numpy preprocessing
* Flask + REST endpoint for recommendation
* Optional: TF-IDF / KNN / clustering

---

## MongoDB Collections

```
vdio database/
├── users                # Stores login/session info
├── track_votes          # Stores song votes per user
├── spotify_tracks       # Metadata cache from Spotify
├── tutorial_progress    # Tutorial completion tracking
├── user_videos          # User-uploaded videos (future use)
├── challenges           # Challenge entries (title, user, file)
```

---

## Libraries & Technologies Used

### Backend

* Flask
* Flask-CORS
* Flask-Session
* PyMongo
* dotenv, json, os, uuid
* FFmpeg (via subprocess)
* werkzeug (secure uploads)

### Frontend

* HTML5, CSS3
* JavaScript (vanilla)
* Font Awesome
* Google Fonts (Poppins)
* Wavesurfer.js (audio trim)
* YouTube Data API v3
* Spotify Embed API

---

## Setup Instructions

### Requirements

* Python 3.9 or higher
* MongoDB (local or cloud)
* FFmpeg installed

### Installation

```bash
pip install -r requirements.txt
```

### Config Setup

Edit `.env` or your config file:

```ini
DB_URL=mongodb://localhost:27017/
SECRET_KEY=your-secret-key
```

### Run the App

```bash
python app.py
```

Visit: [http://localhost:5000](http://localhost:5000)

---

## Screenshots
Home page
![image](https://github.com/user-attachments/assets/50d53821-ad16-4851-948a-1f21ef831bb0)
Transition page
![image](https://github.com/user-attachments/assets/c864aa82-7765-404c-9af3-c94fa0cb022b)
Music page
![image](https://github.com/user-attachments/assets/56483cd1-35da-43fa-883f-4b4bcaf8d343)
Style page
![image](https://github.com/user-attachments/assets/5124dd84-25f7-44f2-9d1a-ade85923b5b6)
Converter tool
![image](https://github.com/user-attachments/assets/b045fc62-e7d2-456a-8c38-61ca2eec1cf3)
Trimmer tool
![image](https://github.com/user-attachments/assets/94b21aad-9839-4612-88d2-2b64bcb22406)


### UI Pages

* Transition tutorial cards
* Music voting UI
* Challenge uploader form
* Converter and Trimmer tools

### MongoDB Data

* User sessions
* Votes tracking
* Challenge uploads

---

## Author & License

**Developed by:** Joel K Mathews
                  joelkmathews2005@gmail.com

**License:** Educational Use Only. No license currently applied.

---
