from machine import ADC, Pin
import time

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

while True:
    if is_noisy_signal():
        print("Noise detected! Vehicle present")
    else:
        print("Signal is clean.")
    time.sleep(1)

