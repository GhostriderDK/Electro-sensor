import sqlite3

DATABASE = "databases/data.db"

def get_vehicle_data(limit=10):
    try:
        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        cur.execute("SELECT * FROM vehicle_registration ORDER BY id DESC LIMIT ?", (limit,))
        rows = cur.fetchall()
        return rows
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    finally:
        conn.close()
