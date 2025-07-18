# 🎵 Emotion-Based Music Recommender

An intelligent web application that detects a user's emotion from text input and recommends matching music using YouTube search. Users can sign up, generate emotion-based playlists, view history, and manage songs — all within a beautifully designed Flask-based platform.

## 🚀 Features

- 🎤 Emotion Detection via Text (using HuggingFace Transformers)

- 🧠 Valence/Arousal Classification using the DEAM dataset

- 🔍 YouTube Music Search based on detected emotion

- 🗂️ Playlist Creation & Management (Add, Rename, Delete, Reorder)

- 📜 User History Tracking

- 👥 Secure Login/Signup with Password Hashing

- 📊 Basic Analytics & Profile Dashboard

- 🌐 Public Playlist Sharing

## 💡 How It Works

1. Emotion Input: Users type in a sentence like "I feel excited".

2. Emotion Mapping: System first tries exact/fuzzy matching with custom phrases.

3. ML Emotion Detection: If no match, the system uses a HuggingFace transformer model.

4. YouTube Integration: A relevant video is fetched using youtube-search-python.

5. Playlist Management: Users can save the song to a playlist, view history, or share.


## 🛠️ Installation

1. Clone the repository

```bash
git clone https://github.com/LanishFasal/Emotion-Music-Recommender.git
cd Emotion-Music-Recommender
```
2. Create a virtual environment (optional but recommended)

```bash

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```
3. Install dependencies

```bash

pip install -r requirements.txt
```
4. Download the DEAM dataset

Place the file static_annotations_averaged_songs_1_2000.csv under Data/Deam/.

5. Initialize the database

```bash

python create_user.py
```

## ▶️ Run the App

```bash

python app.py
```

Visit http://127.0.0.1:5000 in your browser.


## 🔐 Default Credentials

(Set your own credentials later via signup.)

## 📦 Requirements

See requirements.txt for full list:

- Flask

- Pandas

- Transformers

- Torch

- Scikit-learn

- youtube-search-python

- httpx==0.24.1

## 📸 Screenshots 

<img width="1886" height="809" alt="image" src="https://github.com/user-attachments/assets/70d73d8d-a3a0-408f-80ac-03d231e1d90b" />


## 🧠 Future Improvements

- 🎧 Audio-based emotion detection

- 📱 Mobile-responsive UI

- 🧾 Playlist export/share to Spotify

- 👤 OAuth-based login (Google/Facebook)

- 📈 Personalized recommendation model



