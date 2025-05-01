import sqlite3
import json
from datetime import datetime
import paho.mqtt.client as mqtt

DATABASE = "databases/data.db"
MQTT_BROKER = "localhost"
MQTT_TOPIC = "vehicle/json"

def on_message(client, userdata, message):
    data = message.payload.decode()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"Received MQTT message: {data}")

    try:
        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO vehicle_data (datetime, message) VALUES (?, ?)",
            (now, data),
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    finally:
        conn.close()

def setup_database():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS vehicle_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            datetime TEXT NOT NULL,
            message TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

setup_database()

client = mqtt.Client()
client.on_message = on_message
client.connect(MQTT_BROKER, 1883, 60)
client.subscribe(MQTT_TOPIC)
print("Subscribed to MQTT topic:", MQTT_TOPIC)
client.loop_forever()