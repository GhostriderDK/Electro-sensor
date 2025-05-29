import digitalio
import board
import busio
import adafruit_rfm9x
from time import sleep
from datetime import datetime
import paho.mqtt.client as mqtt
from machine import Pin, ADC, PWM, Timer
import time

# LoRa Configuration
RADIO_FREQ_MHZ = 868.0
CS = digitalio.DigitalInOut(board.CE1)
RESET = digitalio.DigitalInOut(board.D25)
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, RADIO_FREQ_MHZ, baudrate=1000000)
rfm9x.tx_power = 23

# MQTT Configuration
mqtt_broker = "77.33.140.232"
mqtt_port = 1883
mqtt_topic = "vehicle/registration"
client = mqtt.Client()
client.connect(mqtt_broker, mqtt_port, 60)

# Sensor and Pin Configuration
pulse_pin = Pin(13, Pin.OUT)
analog_pin = ADC(Pin(36))  # Sensor output from LM324
battery_pin = ADC(Pin(35))  # Voltage divider for battery
analog_pin.atten(ADC.ATTN_11DB)  # Full range: 3.3V
battery_pin.atten(ADC.ATTN_11DB)

# Default Values
duty_cycle = 13  # In percent
frequency = 60   # In Hz
delay_time = 60  # Delay after pulse
R1 = 100000.0
R2 = 47000.0
AREF = 3.6  # Reference voltage for ESP32 ADC (approximate)

def read_battery_voltage():
    samples = []
    for _ in range(10):
        raw = battery_pin.read()
        vout = (raw / 4095.0) * AREF
        vin = (R1 + R2) * vout / R2
        if vin < 0.9:
            vin = 0
        samples.append(vin)
        time.sleep_ms(10)
    return sum(samples) / len(samples)

def send_data(sensor_val, freq, duty, vin):
    print(f"<{sensor_val}/{freq}/{duty}/{vin:.2f}>")

def generate_pulse():
    global duty_cycle, frequency

    period_us = int(1_000_000 / frequency)
    duty_us = int(duty_cycle * 10)

    # Send pulse
    pulse_pin.on()
    time.sleep_us(duty_us)
    pulse_pin.off()

    # Wait for delay
    time.sleep_us(delay_time)

    # Read sensor value
    raw_value = analog_pin.read()
    processed_value = raw_value // 10

    # Read battery voltage
    vin = read_battery_voltage()

    # Output data
    send_data(processed_value, frequency, duty_cycle, vin)

def listen_and_ack(rfm9x):
    expected_seq = 1
    while True:
        packet = rfm9x.receive(timeout=3)
        if packet is not None:
            try:
                msg = packet.decode("utf-8").strip()
                print(f"Received: {msg}\n")  # Log the raw message

                # Extract the sequence number from the message
                try:
                    received_seq = int(msg.split(",")[0].strip())  # Assuming the sequence number is the first part
                except ValueError:
                    print("Error: Unable to parse sequence number from message.")
                    reply = "Error: Invalid sequence format"
                    rfm9x.send(reply.encode())
                    print(f"Sent: {reply}")
                    sleep(0.1)
                    continue

                if received_seq == expected_seq:
                    # Handle expected sequence
                    if "hello on network" in msg:
                        reply = f"{expected_seq}, pi_1 hello esp32_1 online"
                    elif "ready for operation" in msg:
                        reply = f"{expected_seq}, pi_1 ready confirmed"
                    elif "reg v" in msg:
                        reply = f"{expected_seq}, pi received"

                        # Publish message
                        message = {
                            "timestamp": datetime.now().isoformat(),
                            "vehicle_registered": True
                        }
                        client.publish(mqtt_topic, str(message))
                        print(f"Published to MQTT: {message}")
                    else:
                        reply = f"{expected_seq}, pi ack"
                    rfm9x.send(reply.encode())
                    print(f"Sent: {reply}\n")
                    sleep(0.1)  # Short delay to ensure the message is sent
                    expected_seq += 1
                else:
                    # Handle unexpected sequence numbers
                    print(f"Unexpected sequence received: {received_seq}, expected: {expected_seq}")
                    reply = f"{received_seq}, pi unexpected seq received"
                    rfm9x.send(reply.encode())
                    print(f"Sent: {reply}")
                    sleep(0.1)
                    # Update expected_seq to the received sequence number
                    expected_seq = received_seq
            except UnicodeDecodeError as e:
                print(f"Error decoding packet: {e}")
                print(f"Raw packet: {packet}")
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                client.disconnect()
                break

# Main loop
try:
    last_time = time.ticks_us()
    while True:
        now = time.ticks_us()
        if time.ticks_diff(now, last_time) >= int(1_000_000 / frequency):
            generate_pulse()
            last_time = now
        listen_and_ack(rfm9x)
except KeyboardInterrupt:
    print("Program interrupted. Disconnecting MQTT client...")
    client.disconnect()