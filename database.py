import sqlite3
import hashlib

DB_NAME = "users.db"

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        gmail TEXT UNIQUE,
        password TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        gmail TEXT,
        role TEXT,
        message TEXT
    )
    """)

    conn.commit()
    conn.close()

def signup(gmail, password):
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute(
            "INSERT INTO users (gmail, password) VALUES (?, ?)",
            (gmail, hash_password(password))
        )
        conn.commit()
        conn.close()
        return True
    except:
        return False

def login(gmail, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "SELECT * FROM users WHERE gmail=? AND password=?",
        (gmail, hash_password(password))
    )
    user = c.fetchone()
    conn.close()
    return user is not None

def save_message(gmail, role, message):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "INSERT INTO chat_history (gmail, role, message) VALUES (?, ?, ?)",
        (gmail, role, message)
    )
    conn.commit()
    conn.close()

def get_history(gmail):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "SELECT role, message FROM chat_history WHERE gmail=?",
        (gmail,)
    )
    history = c.fetchall()
    conn.close()
    return history

def clear_history(gmail):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM chat_history WHERE gmail=?", (gmail,))
    conn.commit()
    conn.close()