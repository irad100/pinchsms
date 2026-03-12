from typing import TYPE_CHECKING, ClassVar

import usb.core

if TYPE_CHECKING:
    from pinchsms.core.modem import ATModem


class GenericQuirks:
    """Fallback quirks for standard AT-command modems."""

    name = "Generic AT Modem"
    vendor_id = 0
    product_ids: ClassVar[list[int]] = []

    def matches(self, dev: usb.core.Device) -> bool:
        return True

    def prepare(self, dev: usb.core.Device) -> usb.core.Device:
        return dev

    def get_interface(self) -> int:
        return 0

    def post_connect(self, modem: ATModem) -> None:
        modem.send_at("AT+CMGF=1")
        modem.send_at('AT+CPMS="SM","SM","SM"')
        modem.send_at("AT+CNMI=2,1,0,0,0")
        modem.drain()
