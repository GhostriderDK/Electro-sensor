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

while True:
    packet = rfm9x.receive()
    if packet is not None:
        try:
            message = packet.decode('utf-8')
            print(message)
            if any(char.isdigit() for char in message):
            rfm9x.send(bytes(message, 'utf-8'))
        except UnicodeDecodeError:
            print("Failed to decode packet")
        else:
        print("No packet received")
    sleep(1)