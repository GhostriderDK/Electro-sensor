import digitalio
import board
import busio
import adafruit_rfm9x
from time import sleep

RADIO_FREQ_MHZ = 868.0
CS = digitalio.DigitalInOut(board.CE1)
RESET = digitalio.DigitalInOut(board.D25)
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, RADIO_FREQ_MHZ, baudrate=1000000)
rfm9x.tx_power = 23

def listen_and_ack(rfm9x):
    expected_seq = 1
    while True:
        packet = rfm9x.receive(timeout=3)
        if packet is not None:
            try:
                msg = packet.decode("utf-8").strip()
                print(f"Received: {msg}")  # Log the raw message

                # Extract the sequence number from the message
                try:
                    received_seq = int(msg.split(",")[0].strip())  # Assuming the sequence number is the first part
                    print("seq received: ", received_seq)
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
                    else:
                        reply = f"{expected_seq}, pi ack"
                    rfm9x.send(reply.encode())
                    print(f"Sent: {reply}")
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

listen_and_ack(rfm9x)