import time
from typing import TYPE_CHECKING

import usb.core

from pinchsms.core.sms import SmsMessage, parse_message_listing

if TYPE_CHECKING:
    from usb.core import Device, Endpoint


class ModemError(Exception):
    pass


class ATModem:
    """Generic AT command interface for USB modems."""

    def __init__(self, dev: Device, ep_out: Endpoint, ep_in: Endpoint) -> None:
        self.dev = dev
        self.ep_out = ep_out
        self.ep_in = ep_in

    def send_at(self, cmd: str, wait: float = 1.0) -> str:
        """Send an AT command and return the response."""
        self.ep_out.write((cmd + "\r\n").encode())
        time.sleep(wait)
        return self._read_response()

    def _read_response(self, timeout: int = 500) -> str:
        result = b""
        while True:
            try:
                data = self.ep_in.read(512, timeout=timeout)
                result += bytes(data)
            except usb.core.USBTimeoutError:
                break
        return result.decode("utf-8", errors="replace")

    def drain(self) -> None:
        """Discard any pending data from the modem."""
        self._read_response(timeout=100)

    def read_sms(self) -> list[SmsMessage]:
        """Read all SMS messages from SIM."""
        raw = self.send_at('AT+CMGL="ALL"', wait=2.0)
        return parse_message_listing(raw)

    def delete_sms(self, index: int) -> None:
        """Delete an SMS by index."""
        self.send_at(f"AT+CMGD={index}")

    def send_sms(self, number: str, text: str) -> str:
        """Send an SMS message. Returns modem response."""
        self.ep_out.write(f'AT+CMGS="{number}"\r\n'.encode())
        time.sleep(0.5)
        self._read_response(timeout=200)
        self.ep_out.write((text + "\x1a").encode())
        time.sleep(3)
        return self._read_response()

    def check_notifications(self) -> bool:
        """Check for unsolicited +CMTI notifications."""
        urc = self._read_response(timeout=100)
        return "+CMTI" in urc

    def disconnect(self) -> None:
        """Release the USB interface."""
        if self.dev:
            import contextlib

            with contextlib.suppress(Exception):
                usb.util.release_interface(self.dev, 0)
            self.dev = None
            self.ep_out = None
            self.ep_in = None

    @property
    def connected(self) -> bool:
        return self.dev is not None
