import subprocess
import time

import usb.core
import usb.util

VENDOR_ID = 0x1BBB
PRODUCT_STORAGE = 0xF00E
PRODUCT_MODEM = 0x011E
INTF_NUM = 3


class ModemError(Exception):
    pass


class Modem:
    def __init__(self):
        self.dev = None
        self.ep_out = None
        self.ep_in = None

    def connect(self):
        """Find and connect to the modem, mode-switching if needed."""
        dev = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_MODEM)
        if dev is None:
            dev = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_STORAGE)
            if dev is None:
                raise ModemError("Modem not found on USB bus")
            self._mode_switch()
            time.sleep(3)
            dev = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_MODEM)
            if dev is None:
                raise ModemError(
                    "Modem found in storage mode but mode-switch failed"
                )

        cfg = dev.get_active_configuration()
        try:
            if dev.is_kernel_driver_active(INTF_NUM):
                dev.detach_kernel_driver(INTF_NUM)
        except Exception:
            pass

        usb.util.claim_interface(dev, INTF_NUM)
        intf = cfg[(INTF_NUM, 0)]

        ep_out = ep_in = None
        for ep in intf:
            direction = usb.util.endpoint_direction(ep.bEndpointAddress)
            ep_type = usb.util.endpoint_type(ep.bmAttributes)
            if (
                direction == usb.util.ENDPOINT_OUT
                and ep_type == usb.util.ENDPOINT_TYPE_BULK
            ):
                ep_out = ep
            elif (
                direction == usb.util.ENDPOINT_IN
                and ep_type == usb.util.ENDPOINT_TYPE_BULK
            ):
                ep_in = ep

        if not ep_out or not ep_in:
            raise ModemError("Could not find bulk endpoints on interface 3")

        self.dev = dev
        self.ep_out = ep_out
        self.ep_in = ep_in

        self.send_at("AT+CMGF=1")
        self.send_at('AT+CPMS="SM","SM","SM"')
        self.send_at("AT+CNMI=2,1,0,0,0")
        self._drain()

    def _mode_switch(self):
        """Eject the virtual CD-ROM to switch from storage to modem mode."""
        result = subprocess.run(
            ["diskutil", "list"],
            capture_output=True,
            text=True,
        )
        for line in result.stdout.splitlines():
            if "HSPA ROUTER" in line or "CD_ROM_Mode_1" in line:
                parts = line.split()
                disk_id = parts[-1]
                disk = disk_id.split("s")[0]
                subprocess.run(
                    ["diskutil", "eject", disk],
                    capture_output=True,
                    text=True,
                )
                return
        raise ModemError("Could not find modem CD-ROM to eject")

    def disconnect(self):
        if self.dev:
            try:
                usb.util.release_interface(self.dev, INTF_NUM)
            except Exception:
                pass
            self.dev = None
            self.ep_out = None
            self.ep_in = None

    @property
    def connected(self):
        return self.dev is not None

    def send_at(self, cmd, wait=1.0):
        """Send an AT command and return the response."""
        self.ep_out.write((cmd + "\r\n").encode())
        time.sleep(wait)
        return self._read_response()

    def _read_response(self, timeout=500):
        result = b""
        while True:
            try:
                data = self.ep_in.read(512, timeout=timeout)
                result += bytes(data)
            except usb.core.USBTimeoutError:
                break
        return result.decode("utf-8", errors="replace")

    def _drain(self):
        self._read_response(timeout=100)

    def read_sms(self):
        """Read all SMS messages from SIM. Returns list of dicts."""
        raw = self.send_at('AT+CMGL="ALL"', wait=2.0)
        return _parse_messages(raw)

    def delete_sms(self, index):
        """Delete an SMS by index."""
        self.send_at(f"AT+CMGD={index}")

    def check_notifications(self):
        """Check for unsolicited +CMTI notifications."""
        urc = self._read_response(timeout=100)
        return "+CMTI" in urc


def _parse_messages(raw):
    messages = []
    lines = raw.strip().split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("+CMGL:"):
            header = line
            body_lines = []
            i += 1
            while i < len(lines):
                cur = lines[i].strip()
                if cur.startswith("+CMGL:") or cur == "OK":
                    break
                if cur:
                    body_lines.append(cur)
                i += 1
            parts = header.split(",")
            idx = parts[0].split(":")[1].strip()
            sender = parts[2].strip().strip('"') if len(parts) > 2 else "?"
            date = (
                ",".join(parts[3:]).strip().strip('"')
                if len(parts) > 3
                else "?"
            )
            messages.append({
                "index": idx,
                "sender": sender,
                "date": date,
                "body": "\n".join(body_lines),
            })
        else:
            i += 1
    return messages
