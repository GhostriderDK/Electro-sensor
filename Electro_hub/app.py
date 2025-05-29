from flask import Flask, render_template
from get_data import get_vehicle_data
import sqlite3
from datetime import datetime

app = Flask(__name__)

DATABASE = "databases/data.db"

def get_first_timestamp():
    """Fetch the earliest timestamp from the database."""
    try:
        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        cur.execute("SELECT timestamp FROM vehicle_registration ORDER BY id ASC LIMIT 1")
        row = cur.fetchone()
        print(f"First timestamp fetched: {row[0] if row else 'No data'}")
        return row[0] if row else None
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return None
    finally:
        conn.close()

@app.route("/")
def index():
    # Get the latest 25 registrations
    rows = get_vehicle_data(limit=10)

    # Get the first timestamp from the database
    first_timestamp = get_first_timestamp()

    # Calculate uptime
    if first_timestamp:
        try:
            # Use the correct format to parse the timestamp
            first_time = datetime.fromisoformat(first_timestamp)
            now = datetime.now()
            uptime_delta = now - first_time
            uptime = str(uptime_delta).split(".")[0]  # Remove microseconds
        except (ValueError, TypeError) as e:
            print(f"Error parsing first_timestamp: {e}")
            uptime = "Invalid timestamp format"
    else:
        uptime = "Ingen data endnu"

    # Get the last registration timestamp
    last_registration = rows[0][1] if rows else None

    return render_template(
        "index.html",
        uptime=uptime,
        last_registration=last_registration,
        registrations=rows
    )


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5500, debug=True)