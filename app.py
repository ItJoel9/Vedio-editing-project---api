from flask import (
    Flask, request, jsonify, render_template,
    send_file, session, redirect, url_for, send_from_directory
)
from flask import render_template_string

from spotipy.exceptions import SpotifyException
import traceback
from collections import defaultdict
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from flask_pymongo import PyMongo
from flask_cors import CORS
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from bson.objectid import ObjectId
from datetime import datetime, timezone
datetime.now(timezone.utc)
from dotenv import load_dotenv
load_dotenv()

from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.exceptions import SpotifyException

from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from dotenv import load_dotenv
from pydub import AudioSegment
from collections import defaultdict
from datetime import datetime
import os, uuid, time, json, tempfile
from flask import Blueprint

# === ENABLE LOCAL OAUTH === #
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# === INIT FLASK === #
load_dotenv()
app = Flask(__name__)
CORS(app)

# === SESSION CONFIG === #
app.secret_key = "vdio_secret_upload_key"
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = os.path.join(os.getcwd(), "flask_sessions")
app.config["SESSION_PERMANENT"] = False
Session(app)

# === MONGO CONFIG === #
app.config["MONGO_URI"] = "mongodb://localhost:27017/vdio"
mongo = PyMongo(app)

# === UPLOAD SETTINGS === #
# === APP CONFIG === #
app.config["UPLOAD_FOLDER"] = os.path.join("static", "uploads")
app.config["TEMP_SESSION"] = os.path.join("temp_sessions")
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024  # 100MB


# Ensure both directories exist
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["TEMP_SESSION"], exist_ok=True)


# === YOUTUBE API SCOPES === #
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
REDIRECT_URI = "http://localhost:5000/oauth2callback"


recommend_bp = Blueprint('recommend', __name__)
# === EXPORT TO YOUTUBE === #


@app.route("/oauth2callback")
def oauth2callback():
    file_id = request.args.get("state")
    session_path = os.path.join(app.config["TEMP_SESSION"], f"{file_id}.json")

    if not file_id or not os.path.exists(session_path):
        return "<h2 style='color:red;'>❌ Error: No video file found. Try exporting again.</h2>"

    with open(session_path) as f:
        data = json.load(f)

    if not os.path.exists(data["filepath"]):
        return "<h2 style='color:red;'>❌ Video file no longer exists. Try exporting again.</h2>"

    try:
        flow = Flow.from_client_secrets_file(
            "client_secret.json",
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )
        flow.fetch_token(authorization_response=request.url)
        creds = flow.credentials
        youtube = build("youtube", "v3", credentials=creds)
    except Exception as e:
        return f"<h1 style='color:red;'>❌ OAuth Error</h1><pre>{str(e)}</pre>"

    request_body = {
        "snippet": {
            "title": data.get("title", "Untitled"),
            "description": data.get("description", ""),
            "categoryId": "22"
        },
        "status": {
            "privacyStatus": "public"
        }
    }

    media = MediaFileUpload(
        data["filepath"],
        mimetype="video/mp4",
        resumable=True
    )

    try:
        upload_request = youtube.videos().insert(
            part="snippet,status",
            body=request_body,
            media_body=media
        )

        max_attempts = 5
        for attempt in range(max_attempts):
            try:
                upload_response = upload_request.execute()
                break
            except Exception as e:
                print(f"[Attempt {attempt+1}] Upload error: {e}")
                if attempt == max_attempts - 1:
                    raise
                time.sleep(2)

        video_id = upload_response['id']
        return f"""
        <h1 style='color: green;'>✅ Upload Successful!</h1>
        <p>Video ID: <code>{video_id}</code></p>
        <a href="https://www.youtube.com/watch?v={video_id}" target="_blank">🎬 Watch on YouTube</a>
        """

    except Exception as e:
        return f"""
        <h1 style='color:red;'>❌ Upload Failed</h1>
        <pre>{str(e)}</pre>
        """

@app.route("/upload_video", methods=["POST"])
def upload_video():
    platform = request.form.get("platform")
    video = request.files.get("file")

    if not video:
        return jsonify({"message": "No video uploaded."}), 400

    filename = f"{uuid.uuid4().hex}_{video.filename}"
    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    video.save(path)

    file_id = uuid.uuid4().hex
    session_data = {
        "filepath": path,
        "title": request.form.get("title", "Untitled Video"),
        "description": request.form.get("description", "")
    }

    with open(os.path.join(app.config["TEMP_SESSION"], f"{file_id}.json"), "w") as f:
        json.dump(session_data, f)

    if platform == "youtube":
        flow = Flow.from_client_secrets_file(
            "client_secret.json",
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )
        auth_url, _ = flow.authorization_url(prompt="consent", state=file_id)
        return redirect(auth_url)

    return jsonify({"message": f"Video saved to {filename}. Upload manually to {platform.capitalize()}."})

# == Dashboard == #
@app.route('/upload_dashboard_video', methods=['POST'])
def upload_dashboard_video():
    file = request.files.get('dashboard_video')
    if not file:
        return {"message": "No video uploaded."}, 400

    filename = secure_filename(file.filename)
    unique_name = f"{uuid.uuid4().hex[:8]}_{filename}"
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
    file.save(save_path)

    mongo.db.user_videos.insert_one({
        "filename": unique_name
    })

    return redirect(url_for('dashboard'))


# === Audio === #
@app.route("/trim_audio", methods=["POST"])
def trim_audio():
    audio_file = request.files.get("audio")
    start = float(request.form.get("start", 0))
    end = float(request.form.get("end", 0))
    trim_mode = request.form.get("trim_mode", "keep")  # "keep" or "remove"

    if not audio_file or start >= end:
        return "Invalid request", 400

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_in:
        audio_file.save(temp_in.name)

        try:
            original_audio = AudioSegment.from_file(temp_in.name)
        except Exception as e:
            print(f"❌ Audio decode error: {e}")
            return "Failed to process audio", 400

        # Apply keep/remove logic
        if trim_mode == "keep":
            trimmed_audio = original_audio[start * 1000:end * 1000]
        else:
            before = original_audio[:start * 1000]
            after = original_audio[end * 1000:]
            trimmed_audio = before + after

        # Export the trimmed file
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_out:
            trimmed_audio.export(temp_out.name, format="mp3")
            return send_file(temp_out.name, as_attachment=True, download_name="trimmed_audio.mp3")


# === SPOTIFY === #
sp = Spotify(auth_manager=SpotifyClientCredentials(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET")
))

@app.route("/log_genre", methods=["POST"])
def log_genre():
    data = request.get_json()
    if "email" in data and "genre" in data:
        mongo.db.user_genre_logs.insert_one({
            "user_email": data["email"],
            "genre": data["genre"],
            "timestamp": datetime.utcnow()
        })
        return jsonify({"msg": "Logged"}), 200
    return jsonify({"msg": "Missing genre or email"}), 400

from collections import defaultdict
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

@app.route("/music")
def music_page():
    genres = {
        "lofi": ["5mu8Az12kwWkPZKAxAUjnK"],
        "insta": ["0dBhCz84CQZMAXStgbabg2"],
        "new_releases": ["0PMKjSoU937cvzkHpFJ3hf"],
        "tik_tok": ["5iYeSAR4fs2XXnSzjowQ9l"],
        "epic": ["17kf5gMvi1Pm5A0B6NO0t1"],
        "cinematic": ["5cSHyACPfenLmnSquQB0QF"],
        "chill": ["4dsbKfOKg0BrbNqplQxn6G"],
        "trap": ["6KOl9r3nKBYlI69cNVzYy5"],
        "phonk": ["0w21WBF0G1etrYcSudJRMu"],
        "emotional": ["0sNN1PcekOTCz1XNpXazk0"]
    }

    genre_tracks = defaultdict(list)

    for tag, playlist_ids in genres.items():
        for pid in playlist_ids:
            try:
                results = sp.playlist_tracks(pid)
                for item in results["items"]:
                    track = item.get("track")
                    if track:
                        genre_tracks[tag].append({
                            "title": track["name"],
                            "artist": track["artists"][0]["name"],
                            "spotify_id": track["id"]
                        })
            except SpotifyException as e:
                print(f"❌ Error fetching {pid}: {e}")
                continue

    # Limit to top 10 tracks per genre
    for tag in genre_tracks:
        genre_tracks[tag] = genre_tracks[tag][:10]

    return render_template("music.html", genre_tracks=genre_tracks)


# === AUTH === #
@app.route("/auth/register", methods=["POST"])
def register():
    data = request.get_json()
    if mongo.db.users.find_one({"email": data["email"]}):
        return jsonify({"msg": "User already exists"}), 409
    hashed_pw = generate_password_hash(data["password"])
    mongo.db.users.insert_one({
        "name": data["name"],
        "email": data["email"],
        "password": hashed_pw,
        "pfp": "uploads/default_pfp.png"
    })
    return jsonify({"msg": "Registered"}), 201

@app.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    user = mongo.db.users.find_one({"email": data["email"]})

    if user and check_password_hash(user["password"], data["password"]):
        role = user.get("role", "user")
        user_id = str(user["_id"])

        # ✅ Set session values
        session["user_id"] = user_id
        session["email"] = user["email"]
        session["role"] = role

        # ✅ Return user_id in the response
        return jsonify({
            "msg": "Login successful",
            "user_id": user_id,  # 🔥 This is the key line
            "email": user["email"],
            "name": user["name"],
            "role": role,
            "pfp": user.get("pfp", "uploads/default_pfp.png"),
            "redirect": "/admin" if role == "admin" else "/home"
        }), 200

    return jsonify({"msg": "Invalid credentials"}), 401

# == Challenges == #
@app.route("/admin/approve_challenge", methods=["POST"])
def approve_challenge():
    if session.get('role') != 'admin':
        return "Unauthorized", 403
    title = request.json.get("title")
    mongo.db.challenges.update_one({"title": title}, {"$set": {"status": "approved"}})
    return "Challenge approved"

@app.route("/admin/reject_challenge", methods=["POST"])
def reject_challenge():
    if session.get('role') != 'admin':
        return "Unauthorized", 403
    title = request.json.get("title")
    mongo.db.challenges.update_one({"title": title}, {"$set": {"status": "rejected"}})
    return "Challenge rejected"

@app.route("/submit_challenge", methods=["POST"])
def submit_challenge():
    data = request.get_json()
    mongo.db.challenges.insert_one({
        "title": data["title"],
        "user": data["user"],
        "status": "pending"
    })
    return jsonify({"msg": "Challenge submitted!"}), 200

@app.route("/update_exp", methods=["POST"])
def update_exp():
    data = request.get_json()
    user_id = data.get("user_id")
    exp_to_add = data.get("exp")

    if not user_id or exp_to_add is None:
        return jsonify({"error": "Missing data"}), 400

    try:
        print("🛠️ Received EXP update request:", data)

        result = mongo.db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$inc": {"exp": int(exp_to_add)}}
        )

        if result.modified_count == 0:
            return jsonify({"error": "User not found"}), 404

        return jsonify({
            "message": "EXP updated",
            "user_id": user_id,
            "exp_added": exp_to_add
        }), 200

    except Exception as e:
        print("❌ EXP update error:", e)
        return jsonify({"error": "Server error"}), 500

@app.route("/get_user_exp", methods=["POST"])
def get_user_exp():
    data = request.get_json()
    user_id = data.get("user_id")
    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return jsonify({"exp": 0})
    return jsonify({"exp": user.get("exp", 0)})



@app.route("/get_user_info")
def get_user_info():
    email = request.args.get("email")
    user = mongo.db.users.find_one({"email": email})
    if user:
        return jsonify({
            "email": user["email"],
            "name": user["name"],
            "pfp": user.get("pfp", "uploads/default_pfp.png")
        })
    return jsonify({"error": "User not found"}), 404

# === STATIC ROUTES === #
@app.route("/")
def root(): return render_template("login.html")
@app.route("/login")
def login_page(): return render_template("login.html")
@app.route("/register")
def register_page(): return render_template("register.html")
@app.route('/dashboard')
def dashboard():
    user = mongo.db.users.find_one({"email": session["email"]})
    return render_template("dashboard.html",
        user_name=user["name"],
        user_email=user["email"],
        user_exp=user.get("exp", 0),
        user_profile_pic=user.get("profile_pic", "default_pfp.png")
    )


@app.route("/transitions")
def transitions_page(): return render_template("transitions.html")
@app.route("/styles")
def styles_page(): return render_template("styles.html")
@app.route("/platforms")
def platforms_page(): return render_template("platforms.html")
@app.route("/apps")
def apps_page(): return render_template("apps.html")
@app.route("/converter")
def converter_page(): return render_template("converter.html")
@app.route("/trimmer")
def trimmer_page(): return render_template("trimmer.html")
@app.route("/grading")
def grading_page(): return render_template("grading.html")
@app.route("/challenges")
def challenges_page(): return render_template("challenges.html")

@app.route("/admin")
def admin_panel():
    if session.get('role') != 'admin':
        return redirect(url_for('login_page'))

    users = list(mongo.db.users.find({}, {"_id": 0, "name": 1, "email": 1, "role": 1}))
    challenges = list(mongo.db.challenges.find({}, {"_id": 0, "title": 1, "user": 1}))

    stats = {
        "user_count": mongo.db.users.count_documents({}),
        "tool_uses": mongo.db.tool_logs.count_documents({}),
        "challenge_count": mongo.db.challenges.count_documents({}),
        "visits": 1200  # placeholder for now
    }

    return render_template("admin.html", users=users, challenges=challenges, **stats)


@app.route("/admin/delete_user", methods=["DELETE"])
def delete_user():
    if session.get('role') != 'admin':
        return "Unauthorized", 403

    email = request.args.get("email")
    result = mongo.db.users.delete_one({"email": email})
    return "Deleted" if result.deleted_count else "User not found"


@app.route("/home")
def home(): return render_template("vedio_editing.html")
@app.route("/editor")
def editor(): return render_template("vedio_maker_test.html")
@app.route("/zoom_transition")
def zoom_transition(): return render_template("zoom_transition.html")
@app.route("/glitch_flicker")
def glitch_flicker(): return render_template("glitch_flicker.html")
@app.route("/smooth_swipe")
def smooth_swipe(): return render_template("smooth_swipe.html")

@app.route("/transition_tutorial")
def transition_tutorial():
    video_id = request.args.get("vid")
    user_id = session.get("user_id", "guest")
    return render_template("transition_tutorial.html", video_id=video_id, user_id=user_id)


from flask import request, jsonify, session
from datetime import datetime, timezone

from datetime import datetime, timezone
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
import os

# Spotify setup (already in your app, shown here for clarity)
sp = Spotify(auth_manager=SpotifyClientCredentials(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET")
))

def is_valid_spotify_id(track_id):
    return isinstance(track_id, str) and len(track_id) == 22

def fetch_and_store_track_features(track_id):
    if mongo.db.spotify_tracks.find_one({"track_id": track_id}):
        return

    try:
        track = sp.track(track_id)
        audio = sp.audio_features(track_id)[0]

        mongo.db.spotify_tracks.insert_one({
            "track_id": track_id,
            "name": track["name"],
            "artist": track["artists"][0]["name"],
            "album": track["album"]["name"],
            "preview_url": track.get("preview_url"),
            "cover_url": track["album"]["images"][0]["url"] if track["album"]["images"] else "",
            "features": {
                "danceability": audio.get("danceability"),
                "energy": audio.get("energy"),
                "acousticness": audio.get("acousticness"),
                "instrumentalness": audio.get("instrumentalness"),
                "valence": audio.get("valence"),
                "tempo": audio.get("tempo")
            },
            "timestamp": datetime.now(timezone.utc)
        })
    except Exception as e:
        print(f"❌ Error fetching Spotify track {track_id}:", e)


@app.route("/vote_track", methods=["POST"])
def vote_track():
    data = request.get_json()
    user_id = session.get("user_id", "guest")
    track_id = data.get("track_id")
    vote = data.get("vote")

    if not track_id:
        return jsonify({"error": "Missing track_id"}), 400
    if vote not in ["like", "dislike", None]:
        return jsonify({"error": "Invalid vote"}), 400

    if vote is None:
        mongo.db.track_votes.delete_one({"user_id": user_id, "track_id": track_id})
    else:
        mongo.db.track_votes.update_one(
            {"user_id": user_id, "track_id": track_id},
            {"$set": {"vote": vote, "timestamp": datetime.now(timezone.utc)}},
            upsert=True
        )
        if vote == "like":
            fetch_and_store_track_features(track_id)

    return jsonify({"status": "ok"})



from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from flask import jsonify

@app.route("/upload_profile_pic", methods=["POST"])
def upload_profile_pic():
    if "file" not in request.files:
        return jsonify({"status": "fail", "msg": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"status": "fail", "msg": "No selected file"}), 400

    filename = secure_filename(file.filename)
    ext = filename.rsplit('.', 1)[-1]
    unique_filename = f"{uuid.uuid4().hex}.{ext}"

    save_dir = os.path.join("static", "uploads", "pfps")
    os.makedirs(save_dir, exist_ok=True)  # Ensure folder exists
    save_path = os.path.join(save_dir, unique_filename)

    try:
        file.save(save_path)
        mongo.db.users.update_one(
            {"email": session["email"]},
            {"$set": {"profile_pic": unique_filename}}
        )
        return jsonify({"status": "success", "filename": unique_filename})
    except Exception as e:
        print("Upload error:", e)
        return jsonify({"status": "fail", "msg": "Upload failed."}), 500
    

@app.route("/api/user_id")
def get_user_id():
    return jsonify({"user_id": session.get("user_id")})

@app.route("/recommend_test")
def recommend_test_page():
    return render_template("recommend_test.html")

@app.route("/api/spotify_recommendations")
def spotify_recommendations():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    liked_votes = list(mongo.db.track_votes.find({"user_id": user_id, "vote": "like"}))
    liked_track_ids = [vote["track_id"] for vote in liked_votes if isinstance(vote.get("track_id"), str) and len(vote["track_id"]) == 22]

    if not liked_track_ids:
        return jsonify({"error": "No liked tracks found"}), 400

    liked_tracks = list(mongo.db.spotify_tracks.find({"track_id": {"$in": liked_track_ids}}))

    liked_albums = {track.get("album", "") for track in liked_tracks}
    liked_artists = {track.get("artist", "") for track in liked_tracks}

    recommendations = list(mongo.db.spotify_tracks.find({
        "$or": [
            {"album": {"$in": list(liked_albums)}},
            {"artist": {"$in": list(liked_artists)}}
        ],
        "track_id": {"$nin": liked_track_ids}
    }).limit(20))

    if not recommendations:
        return jsonify({"error": "No similar tracks found"}), 404

    results = []
    for track in recommendations:
        results.append({
            "track_id": track.get("track_id", ""),  # ✅ added this
            "title": track.get("name", "Unknown"),
            "artist": track.get("artist", ""),
        })

    return jsonify(results)



@app.route("/fix_missing_features")
def fix_missing_features():
    user_id = session.get("user_id")
    if not user_id:
        return "Login required"

    liked_votes = list(mongo.db.track_votes.find({"user_id": user_id, "vote": "like"}))
    liked_track_ids = [vote["track_id"] for vote in liked_votes]

    fixed = 0
    for tid in liked_track_ids:
        track = mongo.db.spotify_tracks.find_one({"track_id": tid})
        if not track:
            continue
        if "features" not in track or not track["features"]:
            try:
                audio = sp.audio_features(tid)[0]
                mongo.db.spotify_tracks.update_one(
                    {"track_id": tid},
                    {"$set": {"features": audio}}
                )
                fixed += 1
            except:
                print("❌ Couldn't fix features for:", tid)

    return f"<h2>✅ Fixed features for {fixed} liked tracks</h2>"


@app.route("/recommendations/<user_id>")
def recommend_tracks(user_id):
    liked_ids = [doc["track_id"] for doc in mongo.db.track_votes.find({"user_id": user_id, "vote": "like"})]
    if not liked_ids:
        return jsonify({"error": "No liked tracks found"}), 404

    all_tracks = list(mongo.db.spotify_tracks.find({"features": {"$ne": None}}))
    if not all_tracks:
        return jsonify({"error": "No track features found"}), 404

    feature_keys = ["danceability", "energy", "acousticness", "instrumentalness", "valence", "tempo"]
    X, track_meta, liked_vecs = [], [], []

    for track in all_tracks:
        feats = track.get("features", {})
        if all(k in feats for k in feature_keys):
            vec = [feats[k] for k in feature_keys]
            X.append(vec)
            track_meta.append({
                "track_id": track.get("track_id"),
                "name": track.get("name", "Unknown"),
                "artist": track.get("artist", ""),
                "album": track.get("album", ""),
                "preview_url": track.get("preview_url", ""),  # ✅ NEW
                "cover_url": track.get("cover_url", "")       # ✅ NEW
            })
            if track["track_id"] in liked_ids:
                liked_vecs.append(vec)

    if not liked_vecs:
        return jsonify({"error": "No usable liked tracks"}), 400

    avg_vec = np.mean(liked_vecs, axis=0).reshape(1, -1)
    similarities = cosine_similarity(np.array(X), avg_vec).flatten()

    recommendations = []
    for i, meta in enumerate(track_meta):
        tid = meta["track_id"]
        if tid not in liked_ids and is_valid_spotify_id(tid):
            meta["similarity"] = float(similarities[i])
            recommendations.append(meta)

    recommendations.sort(key=lambda x: x["similarity"], reverse=True)
    return jsonify(recommendations[:20])

@app.route("/build_spotify_tracks_metadata_only")
def build_spotify_tracks_metadata_only():
    playlists = [
        "5mu8Az12kwWkPZKAxAUjnK"
    ]

    inserted = 0
    skipped = 0
    errors = 0

    for pid in playlists:
        try:
            print(f"\n🎧 Fetching playlist: {pid}")
            results = sp.playlist_tracks(pid)
            print(f"✅ {len(results['items'])} tracks found in {pid}")
        except Exception as e:
            print(f"❌ Error fetching playlist {pid}")
            traceback.print_exc()
            errors += 1
            continue

        for item in results["items"]:
            track = item.get("track")
            if not track or not track.get("id"):
                print("⚠️ Skipped null or missing track ID")
                skipped += 1
                continue

            track_id = track["id"]

            try:
                mongo.db.spotify_tracks.update_one(
                    {"track_id": track_id},
                    {
                        "$set": {
                            "track_id": track_id,
                            "name": track.get("name", "Unknown"),
                            "artist": track["artists"][0].get("name", "Unknown"),
                            "album": track.get("album", {}).get("name", "Unknown"),
                            "features": {}  # Leave it blank for now
                        }
                    },
                    upsert=True
                )
                print(f"✅ Inserted {track['name']} ({track_id})")
                inserted += 1
            except Exception as e:
                print(f"❌ DB insert failed for {track_id}")
                traceback.print_exc()
                errors += 1

    return render_template_string("""
        <h2 style='font-family:monospace; line-height:1.8'>
        ✅ Inserted: {{ inserted }}<br>
        ⚠️ Skipped: {{ skipped }}<br>
        ❌ Errors: {{ errors }}
        </h2>
    """, inserted=inserted, skipped=skipped, errors=errors)

@app.route("/upgrade_spotify_features")
def upgrade_spotify_features():
    updated = 0
    skipped = 0

    tracks = mongo.db.spotify_tracks.find({"features": {}})
    for track in tracks:
        track_id = track.get("track_id")
        if not track_id:
            skipped += 1
            continue

        try:
            features = sp.audio_features([track_id])[0]
            if not features:
                skipped += 1
                continue

            mongo.db.spotify_tracks.update_one(
                {"track_id": track_id},
                {"$set": {
                    "features": {
                        "danceability": features.get("danceability"),
                        "energy": features.get("energy"),
                        "acousticness": features.get("acousticness"),
                        "instrumentalness": features.get("instrumentalness"),
                        "valence": features.get("valence"),
                        "tempo": features.get("tempo")
                    }
                }}
            )
            print(f"🎯 Features added for {track.get('name')}")
            updated += 1
        except Exception as e:
            print(f"❌ Failed on {track_id}")
            traceback.print_exc()
            skipped += 1

    return f"<h2>🎧 Features Updated: {updated}<br>⚠️ Skipped: {skipped}</h2>"


@app.route("/spotify_track_count")
def track_count():
    total = mongo.db.spotify_tracks.count_documents({})
    return f"<h2>Total Tracks in DB: {total}</h2>"

# === AUTO BUILD SPOTIFY TRACKS IF EMPTY ===
with app.app_context():
    track_count = mongo.db.spotify_tracks.count_documents({})
    if track_count == 0:
        print("⚡ No spotify_tracks found. Auto-building metadata...")
        playlists = ["5mu8Az12kwWkPZKAxAUjnK"]  # you can add more playlists here

        for pid in playlists:
            try:
                results = sp.playlist_tracks(pid)
                for item in results["items"]:
                    track = item.get("track")
                    if track and track.get("id"):
                        track_id = track["id"]
                        mongo.db.spotify_tracks.update_one(
                            {"track_id": track_id},
                            {
                                "$set": {
                                    "track_id": track_id,
                                    "name": track.get("name", "Unknown"),
                                    "artist": track["artists"][0].get("name", "Unknown"),
                                    "album": track.get("album", {}).get("name", "Unknown"),
                                    "features": {}
                                }
                            },
                            upsert=True
                        )
                print(f"✅ Auto-imported songs from playlist {pid}")
            except Exception as e:
                print(f"❌ Error auto-fetching playlist {pid}:", e)
    else:
        print(f"✅ {track_count} tracks already loaded. Skipping auto-build.")


# === RUN === #
if __name__ == "__main__":
    os.makedirs(app.config["SESSION_FILE_DIR"], exist_ok=True)
    app.run(debug=True)
