from flask import Flask, render_template, send_file
from datetime import datetime
from collections import deque
import matplotlib.pyplot as plt
import threading
import time
import paho.mqtt.client as mqtt
import os

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    global last_registration
    payload = msg.payload.decode()
    timestamp = datetime.now()
    last_registration = timestamp
    registrations.append((timestamp, payload))
    print(f"Received: {payload} at {timestamp}")
    generate_graph()

def mqtt_thread():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, 1883, 60)
    client.loop_forever()

def generate_graph():
    times = [r[0] for r in registrations]
    if not times:
        return

    plt.figure(figsize=(8, 3))
    plt.plot(times, range(len(times)), marker='o')
    plt.xlabel("Tidspunkt")
    plt.ylabel("Registrering #")
    plt.title("Registreringstendenser")
    plt.tight_layout()

    os.makedirs("static", exist_ok=True)
    plt.savefig("static/trend.png")
    plt.close()