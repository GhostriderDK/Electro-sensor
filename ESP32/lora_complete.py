from micropython_rfm9x import *
from machine import SPI, Pin, ADC
import time
from time import sleep

RESET = Pin(14, Pin.OUT)
CS = Pin(5, Pin.OUT)
spi = SPI(2, baudrate=1000000, polarity=0, phase=0, bits=8, firstbit=0, sck=Pin(18), mosi=Pin(23), miso=Pin(19))

RADIO_FREQ_MHZ = 868.0
rfm9x = RFM9x(spi, CS, RESET, RADIO_FREQ_MHZ)
button = Pin(35, Pin.IN)
rfm9x.tx_power = 23

def get_time():
    return "12:34"

def send_and_wait_ack(rfm9x, msg, seq, retries=20):
    for _ in range(retries):
        full_msg = f"{seq}, {msg}"
        rfm9x.send(bytes(full_msg, "utf-8"))
        print(f"Sent: {full_msg}")
        start = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start) < 1500:  # 1.5 second timeout
            packet = rfm9x.receive()
            if packet:
                try:
                    resp = packet.decode("utf-8").strip()
                    print(f"Received: {resp}")
                    if "pi unexpected seq received" in resp:
                        print("Unexpected sequence received, resending...")
                        break
                    if f"{seq}" in resp:
                        return True
                except Exception as e:
                    print("Decode failed:", e)
                    print("Raw packet:", packet)
        print("Retrying...")
    return False

adc = ADC(Pin(32))  
adc.atten(ADC.ATTN_11DB)
adc.width(ADC.WIDTH_12BIT)

SAMPLES = 200
SAMPLE_DELAY = 0.02  
CHANGE_THRESHOLD = 100  
NOISE_CHANGE_COUNT = 70  

def is_noisy_signal():
    changes = 0
    prev = adc.read()
    for _ in range(SAMPLES):
        time.sleep(SAMPLE_DELAY)
        current = adc.read()
        if abs(current - prev) > CHANGE_THRESHOLD:
            changes += 1
        prev = current
    print("Detected", changes, "changes")
    return changes > NOISE_CHANGE_COUNT

seq = 1
if send_and_wait_ack(rfm9x, "esp32_1 hello on network", seq):
    seq += 1
    if send_and_wait_ack(rfm9x, "esp32_1 hello pi ready for operation", seq):
        seq += 1
        while True:
            triggered = False
            if button.value() == 1:
                print("Button pressed!")
                triggered = True
            elif is_noisy_signal():
                print("Noise detected! Vehicle present")
                triggered = True
            else:
                print("Signal is clean.")
            if triggered:
                message = f"esp32_1 reg v at {get_time()}"
                if send_and_wait_ack(rfm9x, message, seq):
                    seq += 1
                sleep(5)
            time.sleep(1)