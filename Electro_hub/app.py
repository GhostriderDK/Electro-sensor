from flask import Flask, render_template, send_file
from get_data import get_vehicle_data
import matplotlib.pyplot as plt
import os

app = Flask(__name__)

@app.route("/")
def index():
    data = get_vehicle_data(10)
    return render_template("index.html", data=data)

@app.route("/trend.png")
def trend_image():
    data = get_vehicle_data(10)
    timestamps = [row[1] for row in data]
    messages = range(len(data))

    plt.figure(figsize=(8, 3))
    plt.plot(timestamps, messages, marker='o')
    plt.xlabel("Timestamp")
    plt.ylabel("Message #")
    plt.title("Vehicle Registration Trends")
    plt.tight_layout()

    os.makedirs("static", exist_ok=True)
    plt.savefig("static/trend.png")
    plt.close()
    return send_file("static/trend.png", mimetype="image/png")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5500, debug=True)