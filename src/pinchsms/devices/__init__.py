from pinchsms.core.modem import ATModem, ModemError
from pinchsms.core.usb import claim_interface, find_devices
from pinchsms.devices.generic import GenericQuirks
from pinchsms.devices.sew132 import Sew132Quirks

REGISTRY = [Sew132Quirks(), GenericQuirks()]


def detect_modem(device_name: str = "auto") -> tuple[ATModem, Sew132Quirks | GenericQuirks]:
    """Detect and connect to a USB modem. Returns (modem, quirks)."""
    devices = find_devices()
    if not devices:
        raise ModemError("No USB devices found")

    for quirks in REGISTRY:
        if device_name != "auto" and quirks.name.lower() != device_name.lower():
            continue
        for dev in devices:
            if quirks.matches(dev):
                dev = quirks.prepare(dev)
                intf = quirks.get_interface()
                ep_out, ep_in = claim_interface(dev, intf)
                modem = ATModem(dev, ep_out, ep_in)
                quirks.post_connect(modem)
                return modem, quirks

    raise ModemError(f"No supported modem found (filter: {device_name})")


def list_devices() -> list[dict[str, str | int]]:
    """List all USB devices with vendor/product info."""
    result: list[dict[str, str | int]] = []
    for dev in find_devices():
        matched_quirk = "unknown"
        for quirks in REGISTRY:
            if quirks.matches(dev):
                matched_quirk = quirks.name
                break
        result.append(
            {
                "vendor_id": f"0x{dev.idVendor:04X}",
                "product_id": f"0x{dev.idProduct:04X}",
                "device": matched_quirk,
            }
        )
    return result
