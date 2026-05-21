import time
import config

def scanner_loop():
    while True:
        time.sleep(config.SCAN_INTERVAL)
