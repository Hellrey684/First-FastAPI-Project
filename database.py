import sqlite3

def get_db():
    conn = sqlite3.connect('items.db')
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            is_offer INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()