from micropython_rfm9x import *
from machine import SPI, Pin
import time
from time import sleep

RESET = Pin(14, Pin.OUT)
CS = Pin(5, Pin.OUT)
spi = SPI(2, baudrate=1000000, polarity=0, phase=0, bits=8, firstbit=0, sck=Pin(18), mosi=Pin(23), miso=Pin(19))

RADIO_FREQ_MHZ = 868.0
rfm9x = RFM9x(spi, CS, RESET, RADIO_FREQ_MHZ)
button = Pin(13, Pin.IN)
rfm9x.tx_power = 23

def get_time():
    return "12:34"  # Replace with RTC or other time source if needed

def send_and_wait_ack(rfm9x, msg, seq, retries=20):
    for _ in range(retries):
        full_msg = f"{seq}, {msg}"
        rfm9x.send(bytes(full_msg, "utf-8"))
        print(f"Sent: {full_msg}")
        start = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start) < 3000:  # 3 second timeout
            packet = rfm9x.receive()
            if packet:
                try:
                    resp = packet.decode("utf-8").strip()
                    print(f"Received: {resp}")
                    if f"{seq}" in resp:
                        return True
                    elif "pi unexpected seq received" in resp:
                        print("Unexpected sequence received, resending...")
                        break  # Exit the inner loop to retry sending
                except Exception as e:
                    print("Decode failed:", e)
                    print("Raw packet:", packet)
        print("Retrying...")
    return False

seq = 1
if send_and_wait_ack(rfm9x, "esp32_1 hello on network", seq):
    seq += 1
    if send_and_wait_ack(rfm9x, "esp32_1 hello pi ready for operation", seq):
        seq += 1
        while True:
            if button.value() == 1:
                message = f"esp32_1 reg v at {get_time()}"
                if send_and_wait_ack(rfm9x, message, seq):
                    seq += 1
                sleep(5)
