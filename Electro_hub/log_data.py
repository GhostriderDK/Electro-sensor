import sqlite3
from datetime import datetime
import json
import paho.mqtt.subscribe as subscribe

print("subscribe mqtt script running")
# Create the table if it doesn't exist
def create_table():
    try:
        conn = sqlite3.connect("databases/data.db")
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS vehicle_registration (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                datetime TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                vehicle_registered TEXT NOT NULL
            )
        """)
        conn.commit()
    except sqlite3.Error as sql_e:
        print(f"sqlite error occurred: {sql_e}")
    except Exception as e:
        print(f"Another error occurred: {e}")
    finally:
        conn.close()

create_table()

def vehicle_registration_message(client, userdata, message):
    query = """INSERT INTO vehicle_registration (datetime, timestamp, vehicle_registered) VALUES(?, ?, ?)"""
    now = datetime.now().strftime("%d/%m/%y %H:%M:%S")
    vehicle_data = json.loads(message.payload.decode())  # Decode and parse JSON payload
    
    # Extract fields from the payload
    timestamp = vehicle_data.get('timestamp')
    vehicle_registered = vehicle_data.get('vehicle_registered')
    
    # Prepare data for insertion
    data = (now, timestamp, vehicle_registered)
    
    try:
        conn = sqlite3.connect("databases/data.db")
        cur = conn.cursor()
        cur.execute(query, data)
        conn.commit()
    except sqlite3.Error as sql_e:
        print(f"sqlite error occurred: {sql_e}")
        conn.rollback()
    except Exception as e:
        print(f"Another error occurred: {e}")
    finally:
        conn.close()
        delete_vehicle_registration_data()


def delete_vehicle_registration_data():
    try:
        conn = sqlite3.connect("databases/data.db")
        cur = conn.cursor()
        
        # Delete data points except the 5000 newest
        cur.execute("""
            DELETE FROM vehicle_registration
            WHERE id NOT IN (
                SELECT id
                FROM vehicle_registration
                ORDER BY id DESC
                LIMIT 5000
            )
        """)
        
        conn.commit()
                    
    except sqlite3.Error as sql_e:
        print(f"sqlite error occurred: {sql_e}")
        conn.rollback()

    except Exception as e:
        print(f"Another error occurred: {e}")
    finally:
        conn.close()


topic_function_map = {
    "vehicle/registration": vehicle_registration_message,
}


def on_message_received(client, userdata, message):
    topic = message.topic
    if topic in topic_function_map:
        topic_function_map[topic](client, userdata, message)
    else:
        print(f"No function mapped for topic: {topic}")


topics = ["vehicle/registration"]
subscribe.callback(on_message_received, topics, hostname="localhost", userdata={"message_count": 0})