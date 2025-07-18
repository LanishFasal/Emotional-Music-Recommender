import sqlite3

def init_db():
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    # Users
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL
        )
    ''')

    # History
    cur.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT NOT NULL,
            text TEXT,
            emotion TEXT,
            video_id TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user) REFERENCES users(username)
        )
    ''')

    # Playlists
    cur.execute('''
        CREATE TABLE IF NOT EXISTS playlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT,
            playlist_name TEXT,
            song_id TEXT,
            emotion TEXT,
            FOREIGN KEY(user) REFERENCES users(username)
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ Database initialized.")

if __name__ == "__main__":
    init_db()
