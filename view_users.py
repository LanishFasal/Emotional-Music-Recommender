import sqlite3

conn = sqlite3.connect("users.db")
cursor = conn.cursor()

cursor.execute("SELECT * FROM users")
rows = cursor.fetchall()

print("👤 Users in database:")
for row in rows:
    print(f"Username: {row[0]} | Password: {row[1]}")

conn.close()
