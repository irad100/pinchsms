from typing import TYPE_CHECKING, Protocol  # pragma: no cover

if TYPE_CHECKING:  # pragma: no cover
    from usb.core import Device

    from pinchsms.core.modem import ATModem


class DeviceQuirks(Protocol):  # pragma: no cover
    """Protocol for device-specific behavior."""

    name: str
    vendor_id: int
    product_ids: list[int]

    def matches(self, dev: Device) -> bool:
        """Return True if this quirks class handles the given device."""
        ...

    def prepare(self, dev: Device) -> Device:
        """Prepare the device (e.g. mode-switch). Return the ready device."""
        ...

    def get_interface(self) -> int:
        """Return the USB interface number to claim."""
        ...

    def post_connect(self, modem: ATModem) -> None:
        """Run device-specific AT init commands after connection."""
        ...
