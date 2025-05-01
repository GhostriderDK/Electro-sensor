import digitalio
import board
import busio
import adafruit_rfm9x
from time import sleep
from datetime import datetime
import paho.mqtt.client as mqtt

RADIO_FREQ_MHZ = 868.0
CS = digitalio.DigitalInOut(board.CE1)
RESET = digitalio.DigitalInOut(board.D25)
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, RADIO_FREQ_MHZ, baudrate=1000000)

# MQTT setup
mqtt_broker = "77.33.140.232"
mqtt_port = 1883
mqtt_topic = "vehicle/registration"

# Create MQTT client and connect
client = mqtt.Client()
client.connect(mqtt_broker, mqtt_port, 60)


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
                    expected_seq = received_seq + 1
            except UnicodeDecodeError as e:
                print(f"Error decoding packet: {e}")
                print(f"Raw packet: {packet}")
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                client.disconnect()
                break


try:
    listen_and_ack(rfm9x)
except KeyboardInterrupt:
    print("Program interrupted. Disconnecting MQTT client...")
    client.disconnect()