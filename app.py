from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import pandas as pd
import sqlite3
from transformers import pipeline
from difflib import SequenceMatcher
from datetime import datetime
from youtubesearchpython import VideosSearch
import random
import bcrypt

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Load dataset (optional DEAM dataset with valence/arousal)
df = pd.read_csv("Data/Deam/static_annotations_averaged_songs_1_2000.csv")
df.columns = df.columns.str.strip()
df["emotion"] = df.apply(
    lambda row: (
        "sadness" if row["valence_mean"] < 5 and row["arousal_mean"] < 5 else
        "anger" if row["valence_mean"] < 5 and row["arousal_mean"] >= 5 else
        "joy" if row["valence_mean"] >= 5 and row["arousal_mean"] >= 5 else
        "calm" if row["valence_mean"] >= 5 and row["arousal_mean"] < 5 else
        "neutral"
    ), axis=1
)

# Load HuggingFace emotion classifier
emotion_classifier = pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base")

# Refined emotion map
label_map = {
    "joy": "joy", "happiness": "joy", "excitement": "joy", "love": "joy", "fun": "joy",
    "sadness": "sadness", "depression": "sadness", "grief": "sadness", "heartbreak": "sadness",
    "anger": "anger", "disgust": "anger", "frustration": "anger", "mad": "anger",
    "calm": "calm", "peaceful": "calm", "relaxed": "calm", "content": "calm",
    "surprise": "neutral", "fear": "sadness", "neutral": "neutral", "bored": "neutral"
}

# Custom keyword phrase match
phrase_guide = {
    "i feel calm": "calm",
    "i am calm": "calm",
    "i feel relaxed": "calm",
    "i am relaxed": "calm",
    "i feel peaceful": "calm",
    "i am peaceful": "calm",
    "i feel sad": "sadness",
    "i am sad": "sadness",
    "i feel down": "sadness",
    "i am down": "sadness",
    "i feel happy": "joy",
    "i am happy": "joy",
    "i feel excited": "joy",
    "i am excited": "joy",
    "i feel angry": "anger",
    "i am angry": "anger",
    "i feel mad": "anger",
    "i am mad": "anger",
    "i feel neutral": "neutral",
    "i am neutral": "neutral",
    "i feel bored": "neutral",
    "i am bored": "neutral",
    "i am in party mood": "party",
    # Add more as needed
}

emotion_to_query = {
    "joy": "happy songs",
    "sadness": "sad songs",
    "anger": "angry rock music",
    "calm": "relaxing music",
    "neutral": "chill music",
    "party": "party songs",
    # Add more as needed
}

# Update phrase_guide to map 'party mood' to 'party' emotion
phrase_guide["i am in party mood"] = "party"

phrase_guide.update({
    "i feel rave": "rave",
    "i am at a rave": "rave",
    "i want rave": "rave",
    "i feel like raving": "rave",
    "let's rave": "rave",
    "rave mood": "rave",
    "i am in rave mood": "rave",
    # Add more as needed
})

label_map["rave"] = "rave"

emotion_to_query["rave"] = "rave songs"

# Diverse queries for each mood
party_queries = [
    "English party songs", "Top US party hits", "Latin party music", "EDM party mix", "Pop party anthems",
    "Global party playlist", "K-pop party songs", "Afrobeat party mix", "Best 2000s party songs", "Dance party classics"
]
joy_queries = [
    "happy pop songs", "feel good music", "upbeat dance hits", "classic rock happy songs", "K-pop happy songs",
    "Latin happy music", "Afrobeat happy songs", "indie happy playlist", "best 90s happy songs", "summer hits playlist"
]
sadness_queries = [
    "sad English songs", "heartbreak ballads", "emotional pop songs", "sad K-pop songs", "Latin sad music",
    "Afrobeat sad songs", "classic rock sad songs", "indie sad playlist", "best 2000s sad songs", "melancholy piano music"
]
anger_queries = [
    "angry rock music", "rap songs for anger", "metal rage songs", "EDM aggressive mix", "punk angry anthems",
    "hip hop anger playlist", "K-pop intense songs", "Latin aggressive music", "Afrobeat hype songs", "classic rock power songs"
]
calm_queries = [
    "relaxing acoustic songs", "chillout lounge music", "calm piano playlist", "lofi chill beats", "ambient calm music",
    "K-pop chill songs", "Latin chill music", "Afrobeat relaxing songs", "indie calm playlist", "yoga meditation music"
]
neutral_queries = [
    "chill pop songs", "background study music", "easy listening playlist", "indie neutral songs", "instrumental chill mix",
    "K-pop neutral songs", "Latin easy listening", "Afrobeat chill playlist", "classic rock mellow songs", "coffee shop music"
]
rave_queries = [
    "EDM rave party music", "best rave songs", "rave festival music", "electronic dance rave mix", "rave party mix",
    "trance rave music", "techno rave songs", "hardcore rave music", "global rave anthems", "90s rave classics"
]

def match_phrase(text):
    text = text.lower().strip()
    # Exact match first
    if text in phrase_guide:
        print(f"[DEBUG] Exact phrase match: '{text}' -> {phrase_guide[text]}")
        return phrase_guide[text]
    # Fuzzy match
    best_match = None
    highest_ratio = 0.0
    for phrase in phrase_guide:
        ratio = SequenceMatcher(None, phrase, text).ratio()
        if ratio > highest_ratio:
            highest_ratio = ratio
            best_match = phrase
    if highest_ratio > 0.7:
        print(f"[DEBUG] Fuzzy phrase match: '{text}' ~ '{best_match}' ({highest_ratio:.2f}) -> {phrase_guide[best_match]}")
        return phrase_guide[best_match]
    print(f"[DEBUG] No phrase match for: '{text}' (best fuzzy: '{best_match}' {highest_ratio:.2f})")
    return None

def youtube_search(emotion):
    if emotion == "party":
        query = random.choice(party_queries)
    elif emotion == "joy":
        query = random.choice(joy_queries)
    elif emotion == "sadness":
        query = random.choice(sadness_queries)
    elif emotion == "anger":
        query = random.choice(anger_queries)
    elif emotion == "calm":
        query = random.choice(calm_queries)
    elif emotion == "neutral":
        query = random.choice(neutral_queries)
    elif emotion == "rave":
        query = random.choice(rave_queries)
    else:
        query = emotion_to_query.get(emotion, f"{emotion} music")
    try:
        videosSearch = VideosSearch(query, limit=5)
        results = videosSearch.result()
        if results['result']:
            video = random.choice(results['result'])
            video_id = video['id']
            thumbnail_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
            return video_id, thumbnail_url
    except Exception as e:
        print("YouTube search failed:", e)
    return None, None

# --- Playlist Management DB Setup ---
def init_playlist_db():
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS playlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT,
            name TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS playlist_songs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            playlist_id INTEGER,
            song_id TEXT,
            emotion TEXT,
            added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (playlist_id) REFERENCES playlists(id)
        )
    """)
    conn.commit()
    conn.close()

init_playlist_db()

@app.context_processor
def inject_current_year():
    return {"current_year": datetime.now().year}

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        if not username or not password:
            flash("Username and password are required.")
            return render_template("login.html")
        conn = sqlite3.connect("users.db")
        cur = conn.cursor()
        cur.execute("SELECT password FROM users WHERE username = ?", (username,))
        row = cur.fetchone()
        conn.close()
        if row:
            hashed_pw = row[0]
            if isinstance(hashed_pw, str):
                hashed_pw = hashed_pw.encode('utf-8')
            # Only check if it's a valid bcrypt hash
            if hashed_pw.startswith(b"$2b$") or hashed_pw.startswith(b"$2a$"):
                if bcrypt.checkpw(password.encode('utf-8'), hashed_pw):
                    session["username"] = username
                    flash(f"Welcome, {username}!")
                    return redirect(url_for("dashboard"))
        flash("Invalid credentials")
    return render_template("login.html")

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "username" not in session:
        return redirect(url_for("login"))

    emotion = None
    video_id = None
    thumbnail_url = None

    if request.method == "POST":
        text = request.form.get("text")
        if not text:
            flash("Please enter some text.")
            return redirect(url_for("dashboard"))

        matched_emotion = match_phrase(text)
        if matched_emotion:
            raw_emotion = matched_emotion
            print(f"[DEBUG] Using matched emotion: {raw_emotion}")
        else:
            prediction = emotion_classifier(text)[0]
            raw_emotion = prediction["label"].lower()
            print(f"[DEBUG] Model prediction: {prediction['label']} (raw: {raw_emotion})")

        emotion = label_map.get(raw_emotion, raw_emotion)
        print(f"[DEBUG] Final mapped emotion: {emotion}")

        # Get a YouTube video ID and thumbnail based on detected emotion
        video_id, thumbnail_url = youtube_search(emotion)

        # Save to history
        conn = sqlite3.connect("users.db")
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user TEXT, text TEXT, emotion TEXT, video_id TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute(
            "INSERT INTO history (user, text, emotion, video_id) VALUES (?, ?, ?, ?)",
            (session["username"], text, emotion, video_id)
        )
        conn.commit()
        conn.close()

    return render_template("dashboard.html", username=session["username"], emotion=emotion, video_id=video_id, thumbnail_url=thumbnail_url)

@app.route("/history")
def history():
    if "username" not in session:
        return redirect(url_for("login"))
    conn = sqlite3.connect("users.db")
    df = pd.read_sql_query("SELECT * FROM history WHERE user = ?", conn, params=[session["username"]])
    conn.close()
    return render_template("history.html", history=df.to_dict(orient="records"))

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        if not username or not password:
            flash("Username and password are required.")
            return render_template("signup.html")
        if len(username) < 3 or len(password) < 6:
            flash("Username must be at least 3 characters and password at least 6 characters.")
            return render_template("signup.html")
        conn = sqlite3.connect("users.db")
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT
            )
        """)
        cur.execute("SELECT * FROM users WHERE username = ?", (username,))
        if cur.fetchone():
            flash("Username already exists. Please choose another.")
            conn.close()
            return render_template("signup.html")
        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_pw))
        conn.commit()
        conn.close()
        flash("User created successfully! Please log in.")
        return redirect(url_for("login"))
    return render_template("signup.html")

@app.route("/create_playlist", methods=["GET", "POST"])
def create_playlist():
    if "username" not in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        playlist_name = request.form["playlist_name"].strip()
        if not playlist_name:
            flash("Playlist name is required.")
            return render_template("create_playlist.html")
        conn = sqlite3.connect("users.db")
        cur = conn.cursor()
        cur.execute("INSERT INTO playlists (user, name) VALUES (?, ?)", (session["username"], playlist_name))
        conn.commit()
        conn.close()
        flash("Playlist created!")
        return redirect(url_for("playlist"))
    return render_template("create_playlist.html")

@app.route("/add_to_playlist", methods=["POST"])
def add_to_playlist():
    if "username" not in session:
        return redirect(url_for("login"))
    song_id = request.form["song_id"]
    emotion = request.form["emotion"]
    playlist_name = request.form["playlist_name"].strip()
    if not playlist_name:
        flash("Playlist name is required.")
        return redirect(url_for("dashboard"))
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    # Find or create playlist
    cur.execute("SELECT id FROM playlists WHERE user = ? AND name = ?", (session["username"], playlist_name))
    row = cur.fetchone()
    if row:
        playlist_id = row[0]
    else:
        cur.execute("INSERT INTO playlists (user, name) VALUES (?, ?)", (session["username"], playlist_name))
        playlist_id = cur.lastrowid
    # Add song
    cur.execute("INSERT INTO playlist_songs (playlist_id, song_id, emotion) VALUES (?, ?, ?)", (playlist_id, song_id, emotion))
    conn.commit()
    conn.close()
    flash("Song added to playlist!")
    return redirect(url_for("playlist"))

@app.route("/playlist")
def playlist():
    if "username" not in session:
        return redirect(url_for("login"))
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    # Get all user's playlists
    cur.execute("SELECT id, name FROM playlists WHERE user = ?", (session["username"],))
    playlists = cur.fetchall()
    playlist_data = []
    for pid, name in playlists:
        cur.execute("SELECT id, song_id, emotion FROM playlist_songs WHERE playlist_id = ?", (pid,))
        songs = cur.fetchall()
        playlist_data.append({
            "id": pid,
            "name": name,
            "songs": [{"id": sid, "song_id": song_id, "emotion": emotion} for sid, song_id, emotion in songs]
        })
    conn.close()
    return render_template("playlist.html", playlists=playlist_data)

@app.route("/remove_song/<int:song_id>")
def remove_song(song_id):
    if "username" not in session:
        return redirect(url_for("login"))
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("DELETE FROM playlist_songs WHERE id = ?", (song_id,))
    conn.commit()
    conn.close()
    flash("Song removed from playlist.")
    return redirect(url_for("playlist"))

@app.route("/profile")
def profile():
    if "username" not in session:
        return redirect(url_for("login"))
    # Dummy joined_date for now
    return render_template("profile.html", username=session['username'], joined_date="2024-01-01")

@app.route("/analytics")
def analytics():
    if "username" not in session:
        return redirect(url_for("login"))
    # Dummy emotion data for now
    emotion_data = {"labels": ["Joy", "Sadness", "Anger"], "counts": [5, 2, 1]}
    return render_template("analytics.html", emotion_data=emotion_data)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/rename_playlist/<int:playlist_id>", methods=["POST"])
def rename_playlist(playlist_id):
    if "username" not in session:
        return redirect(url_for("login"))
    new_name = request.form["new_name"].strip()
    if not new_name:
        flash("Playlist name cannot be empty.")
        return redirect(url_for("playlist"))
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("UPDATE playlists SET name = ? WHERE id = ? AND user = ?", (new_name, playlist_id, session["username"]))
    conn.commit()
    conn.close()
    flash("Playlist renamed!")
    return redirect(url_for("playlist"))

@app.route("/delete_playlist/<int:playlist_id>", methods=["POST"])
def delete_playlist(playlist_id):
    if "username" not in session:
        return redirect(url_for("login"))
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("DELETE FROM playlist_songs WHERE playlist_id = ?", (playlist_id,))
    cur.execute("DELETE FROM playlists WHERE id = ? AND user = ?", (playlist_id, session["username"]))
    conn.commit()
    conn.close()
    flash("Playlist deleted!")
    return redirect(url_for("playlist"))

@app.route("/share_playlist/<int:playlist_id>")
def share_playlist(playlist_id):
    # Publicly viewable playlist page (no login required)
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("SELECT name, user FROM playlists WHERE id = ?", (playlist_id,))
    row = cur.fetchone()
    if not row:
        return "Playlist not found", 404
    name, user = row
    cur.execute("SELECT song_id, emotion FROM playlist_songs WHERE playlist_id = ?", (playlist_id,))
    songs = cur.fetchall()
    conn.close()
    playlist = {"id": playlist_id, "name": name, "user": user, "songs": [{"song_id": s, "emotion": e} for s, e in songs]}
    return render_template("playlist.html", playlists=[playlist], public=True)

@app.route("/move_song/<int:song_id>/<string:direction>", methods=["POST"])
def move_song(song_id, direction):
    if "username" not in session:
        return redirect(url_for("login"))
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    # Get playlist_id and current order
    cur.execute("SELECT playlist_id FROM playlist_songs WHERE id = ?", (song_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        flash("Song not found.")
        return redirect(url_for("playlist"))
    playlist_id = row[0]
    # Get all songs in order
    cur.execute("SELECT id FROM playlist_songs WHERE playlist_id = ? ORDER BY id", (playlist_id,))
    songs = [r[0] for r in cur.fetchall()]
    idx = songs.index(song_id)
    if direction == "up" and idx > 0:
        songs[idx], songs[idx-1] = songs[idx-1], songs[idx]
    elif direction == "down" and idx < len(songs)-1:
        songs[idx], songs[idx+1] = songs[idx+1], songs[idx]
    # Reassign ids to reorder (simple way)
    for new_id, sid in enumerate(songs, start=1):
        cur.execute("UPDATE playlist_songs SET id = ? WHERE id = ?", (1000000+new_id, sid))  # temp id to avoid conflict
    for new_id, sid in enumerate(songs, start=1):
        cur.execute("UPDATE playlist_songs SET id = ? WHERE id = ?", (sid, 1000000+new_id))
    conn.commit()
    conn.close()
    return redirect(url_for("playlist"))

if __name__ == "__main__":
    app.run(debug=True)
