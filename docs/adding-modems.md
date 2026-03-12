# Adding Modem Support

## Step 1: Create a Quirks Module

Create `src/pinchsms/devices/yourmodem.py`:

```python
from __future__ import annotations
from typing import TYPE_CHECKING
import usb.core

if TYPE_CHECKING:
    from pinchsms.core.modem import ATModem

VENDOR_ID = 0xXXXX
PRODUCT_ID = 0xXXXX

class YourModemQuirks:
    name = "YourModem"
    vendor_id = VENDOR_ID
    product_ids = [PRODUCT_ID]

    def matches(self, dev: usb.core.Device) -> bool:
        return dev.idVendor == VENDOR_ID and dev.idProduct == PRODUCT_ID

    def prepare(self, dev: usb.core.Device) -> usb.core.Device:
        # Mode-switch logic if needed, or just return dev
        return dev

    def get_interface(self) -> int:
        # USB interface number for AT commands (check with lsusb -v)
        return 0

    def post_connect(self, modem: ATModem) -> None:
        modem.send_at("AT+CMGF=1")
        modem.send_at('AT+CPMS="SM","SM","SM"')
        modem.send_at("AT+CNMI=2,1,0,0,0")
        modem.drain()
```

## Step 2: Register the Quirks

In `src/pinchsms/devices/__init__.py`, add your quirks **before** `GenericQuirks`:

```python
from pinchsms.devices.yourmodem import YourModemQuirks

REGISTRY = [Sew132Quirks(), YourModemQuirks(), GenericQuirks()]
```

## Step 3: Add Tests

In `tests/test_devices.py`:

```python
from pinchsms.devices.yourmodem import YourModemQuirks, VENDOR_ID, PRODUCT_ID

class TestYourModemQuirks:
    def test_matches(self):
        quirks = YourModemQuirks()
        dev = MagicMock()
        dev.idVendor = VENDOR_ID
        dev.idProduct = PRODUCT_ID
        assert quirks.matches(dev) is True
```

## Tips

- Use `lsusb -v` (Linux) or `system_profiler SPUSBDataType` (macOS) to find vendor/product IDs and interface numbers
- Some modems need mode-switching from storage mode (virtual CD-ROM) to modem mode
- The interface number for AT commands varies by device — check the device's USB descriptors
