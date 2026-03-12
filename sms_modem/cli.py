import sys
import time
from datetime import datetime

import usb.core

from sms_modem.modem import Modem, ModemError

POLL_INTERVAL = 5
RECONNECT_DELAY = 10


def main():
    modem = Modem()

    try:
        _run(modem)
    except KeyboardInterrupt:
        _log("Stopped.")
    finally:
        modem.disconnect()


def _run(modem):
    while True:
        if not modem.connected:
            try:
                _log("Connecting to modem...")
                modem.connect()
                _log("Connected. Monitoring for SMS.\n")
            except ModemError as e:
                _log(f"Connection failed: {e}")
                _log(f"Retrying in {RECONNECT_DELAY}s...\n")
                time.sleep(RECONNECT_DELAY)
                continue

        try:
            modem.check_notifications()

            messages = modem.read_sms()
            for msg in messages:
                _log("NEW SMS")
                print(f"  From: {msg['sender']}")
                print(f"  Date: {msg['date']}")
                print(f"  Body: {msg['body']}")
                modem.delete_sms(msg["index"])
                print(f"  (deleted from SIM to free slot)\n")

            time.sleep(POLL_INTERVAL)

        except (usb.core.USBError, ModemError) as e:
            _log(f"USB error: {e}")
            modem.disconnect()
            _log(f"Reconnecting in {RECONNECT_DELAY}s...\n")
            time.sleep(RECONNECT_DELAY)


def _log(msg):
    print(f"[{datetime.now():%H:%M:%S}] {msg}")


if __name__ == "__main__":
    main()
