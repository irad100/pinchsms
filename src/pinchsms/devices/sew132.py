import platform
import subprocess
import time
from typing import TYPE_CHECKING, ClassVar

import usb.core

if TYPE_CHECKING:
    from pinchsms.core.modem import ATModem


VENDOR_ID = 0x1BBB
PRODUCT_STORAGE = 0xF00E
PRODUCT_MODEM = 0x011E


class Sew132Quirks:
    """Quirks for the Strong Rising SEW132 USB modem."""

    name = "SEW132"
    vendor_id = VENDOR_ID
    product_ids: ClassVar[list[int]] = [PRODUCT_STORAGE, PRODUCT_MODEM]

    def matches(self, dev: usb.core.Device) -> bool:
        return dev.idVendor == VENDOR_ID and dev.idProduct in (PRODUCT_STORAGE, PRODUCT_MODEM)

    def prepare(self, dev: usb.core.Device) -> usb.core.Device:
        if dev.idProduct == PRODUCT_MODEM:
            return dev
        self._mode_switch()
        time.sleep(3)
        modem_dev = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_MODEM)
        if modem_dev is None:
            from pinchsms.core.modem import ModemError

            raise ModemError("SEW132 mode-switch failed: modem device not found after eject")
        return modem_dev

    def get_interface(self) -> int:
        return 3

    def post_connect(self, modem: ATModem) -> None:
        modem.send_at("AT+CMGF=1")
        modem.send_at('AT+CPMS="SM","SM","SM"')
        modem.send_at("AT+CNMI=2,1,0,0,0")
        modem.drain()

    def _mode_switch(self) -> None:
        system = platform.system()
        if system == "Darwin":
            self._eject_macos()
        elif system == "Linux":  # pragma: no cover — platform-dependent
            self._eject_linux()
        else:
            from pinchsms.core.modem import ModemError

            raise ModemError(f"SEW132 mode-switch not supported on {system}")

    def _eject_macos(self) -> None:
        from pinchsms.core.modem import ModemError

        result = subprocess.run(
            ["diskutil", "list"],
            capture_output=True,
            text=True,
            check=False,
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
                    check=False,
                )
                return
        raise ModemError("SEW132: could not find modem CD-ROM to eject")

    def _eject_linux(self) -> None:
        from pinchsms.core.modem import ModemError

        result = subprocess.run(
            ["lsblk", "-o", "NAME,MODEL", "-n"],
            capture_output=True,
            text=True,
            check=False,
        )
        for line in result.stdout.splitlines():
            if "HSPA" in line or "CD_ROM" in line:
                dev_name = line.split()[0]
                subprocess.run(
                    ["eject", f"/dev/{dev_name}"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                return
        raise ModemError("SEW132: could not find modem CD-ROM to eject on Linux")
