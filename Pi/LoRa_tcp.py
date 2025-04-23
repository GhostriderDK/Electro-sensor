import digitalio
import board
import busio
import adafruit_rfm9x
from time import sleep

RADIO_FREQ_MHZ = 868.0
CS = digitalio.DigitalInOut(board.CE1)
RESET = digitalio.DigitalInOut(board.D25)
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, RADIO_FREQ_MHZ)
# Initialze RFM radio with a more conservative baudrate
rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, RADIO_FREQ_MHZ, baudrate=1000000)


def listen_and_ack(rfm9x):
    expected_seq = 1
    while True:
        packet = rfm9x.receive(timeout=3)
        if packet is not None:
            msg = packet.decode("utf-8").strip()
            print(f"Received: {msg}")
            if f"seq {expected_seq}" in msg:
                if "hello on network" in msg:
                    reply = f"seq {expected_seq}, pi_1 hello esp32_1 online"
                elif "ready for operation" in msg:
                    reply = f"seq {expected_seq}, pi_1 ready confirmed"
                elif "reg v" in msg:
                    reply = f"seq {expected_seq}, pi received"
                else:
                    reply = f"seq {expected_seq}, pi ack"
                rfm9x.send(reply.encode())
                print(f"Sent: {reply}")
                sleep(0.1)  # Short delay to ensure the message is sent
                expected_seq += 1

listen_and_ack(rfm9x)