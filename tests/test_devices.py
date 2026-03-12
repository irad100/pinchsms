from unittest.mock import MagicMock, patch

import pytest
import usb.core

from pinchsms.core.modem import ModemError
from pinchsms.devices import detect_modem, list_devices
from pinchsms.devices.generic import GenericQuirks
from pinchsms.devices.sew132 import PRODUCT_MODEM, PRODUCT_STORAGE, VENDOR_ID, Sew132Quirks


def _mock_endpoints():
    """Create mock endpoints where ep_in.read raises USBTimeoutError (prevents hang)."""
    ep_out = MagicMock()
    ep_in = MagicMock()
    ep_in.read.side_effect = usb.core.USBTimeoutError("timeout")
    return ep_out, ep_in


class TestSew132Quirks:
    def test_matches_storage_device(self):
        quirks = Sew132Quirks()
        dev = MagicMock()
        dev.idVendor = VENDOR_ID
        dev.idProduct = PRODUCT_STORAGE
        assert quirks.matches(dev) is True

    def test_matches_modem_device(self):
        quirks = Sew132Quirks()
        dev = MagicMock()
        dev.idVendor = VENDOR_ID
        dev.idProduct = PRODUCT_MODEM
        assert quirks.matches(dev) is True

    def test_no_match_wrong_vendor(self):
        quirks = Sew132Quirks()
        dev = MagicMock()
        dev.idVendor = 0xDEAD
        dev.idProduct = PRODUCT_MODEM
        assert quirks.matches(dev) is False

    def test_no_match_wrong_product(self):
        quirks = Sew132Quirks()
        dev = MagicMock()
        dev.idVendor = VENDOR_ID
        dev.idProduct = 0x9999
        assert quirks.matches(dev) is False

    def test_interface_number(self):
        quirks = Sew132Quirks()
        assert quirks.get_interface() == 3

    def test_prepare_already_modem(self):
        quirks = Sew132Quirks()
        dev = MagicMock()
        dev.idProduct = PRODUCT_MODEM
        result = quirks.prepare(dev)
        assert result is dev

    @patch("pinchsms.devices.sew132.usb.core.find")
    @patch("pinchsms.devices.sew132.time.sleep")
    @patch("pinchsms.devices.sew132.subprocess.run")
    @patch("pinchsms.devices.sew132.platform.system", return_value="Darwin")
    def test_prepare_mode_switch_macos(self, mock_sys, mock_run, mock_sleep, mock_find):
        mock_run.return_value = MagicMock(
            stdout="/dev/disk2 (external):\n   #:  TYPE  NAME  SIZE  IDENTIFIER\n"
            "   0:  CD_ROM_Mode_1  HSPA ROUTER  *3.1 MB  disk2\n"
        )
        modem_dev = MagicMock()
        mock_find.return_value = modem_dev

        quirks = Sew132Quirks()
        dev = MagicMock()
        dev.idProduct = PRODUCT_STORAGE
        result = quirks.prepare(dev)
        assert result is modem_dev

    @patch("pinchsms.devices.sew132.usb.core.find", return_value=None)
    @patch("pinchsms.devices.sew132.time.sleep")
    @patch("pinchsms.devices.sew132.subprocess.run")
    @patch("pinchsms.devices.sew132.platform.system", return_value="Darwin")
    def test_prepare_mode_switch_fails(self, mock_sys, mock_run, mock_sleep, mock_find):
        mock_run.return_value = MagicMock(stdout="HSPA ROUTER disk2\n")

        quirks = Sew132Quirks()
        dev = MagicMock()
        dev.idProduct = PRODUCT_STORAGE
        with pytest.raises(ModemError, match="mode-switch failed"):
            quirks.prepare(dev)

    @patch("pinchsms.devices.sew132.subprocess.run")
    @patch("pinchsms.devices.sew132.platform.system", return_value="Darwin")
    def test_eject_macos_no_disk_found(self, mock_sys, mock_run):
        mock_run.return_value = MagicMock(stdout="nothing here\n")
        quirks = Sew132Quirks()
        with pytest.raises(ModemError, match="could not find modem CD-ROM"):
            quirks._eject_macos()

    @patch("pinchsms.devices.sew132.subprocess.run")
    @patch("pinchsms.devices.sew132.platform.system", return_value="Linux")
    def test_eject_linux(self, mock_sys, mock_run):
        mock_run.return_value = MagicMock(stdout="sr0 HSPA Modem\n")
        quirks = Sew132Quirks()
        quirks._eject_linux()
        assert mock_run.call_count == 2

    @patch("pinchsms.devices.sew132.subprocess.run")
    @patch("pinchsms.devices.sew132.platform.system", return_value="Linux")
    def test_eject_linux_no_device(self, mock_sys, mock_run):
        mock_run.return_value = MagicMock(stdout="sda Samsung SSD\n")
        quirks = Sew132Quirks()
        with pytest.raises(ModemError, match="could not find"):
            quirks._eject_linux()

    @patch("pinchsms.devices.sew132.platform.system", return_value="Windows")
    def test_mode_switch_unsupported_platform(self, mock_sys):
        quirks = Sew132Quirks()
        with pytest.raises(ModemError, match="not supported on Windows"):
            quirks._mode_switch()

    def test_post_connect(self):
        quirks = Sew132Quirks()
        modem = MagicMock()
        quirks.post_connect(modem)
        assert modem.send_at.call_count == 3
        modem.drain.assert_called_once()


class TestGenericQuirks:
    def test_matches_anything(self):
        quirks = GenericQuirks()
        dev = MagicMock()
        dev.idVendor = 0x1234
        dev.idProduct = 0x5678
        assert quirks.matches(dev) is True

    def test_interface_zero(self):
        quirks = GenericQuirks()
        assert quirks.get_interface() == 0

    def test_prepare_passthrough(self):
        quirks = GenericQuirks()
        dev = MagicMock()
        result = quirks.prepare(dev)
        assert result is dev

    def test_post_connect(self):
        quirks = GenericQuirks()
        modem = MagicMock()
        quirks.post_connect(modem)
        assert modem.send_at.call_count == 3
        modem.drain.assert_called_once()


class TestDetectModem:
    @patch("pinchsms.devices.find_devices", return_value=[])
    def test_no_devices_raises(self, mock_find):
        with pytest.raises(ModemError, match="No USB devices found"):
            detect_modem()

    @patch("pinchsms.core.modem.time.sleep")
    @patch("pinchsms.devices.claim_interface")
    @patch("pinchsms.devices.find_devices")
    def test_detects_sew132(self, mock_find, mock_claim, mock_sleep):
        dev = MagicMock()
        dev.idVendor = VENDOR_ID
        dev.idProduct = PRODUCT_MODEM
        mock_find.return_value = [dev]
        mock_claim.return_value = _mock_endpoints()

        _modem, quirks = detect_modem()
        assert isinstance(quirks, Sew132Quirks)

    @patch("pinchsms.core.modem.time.sleep")
    @patch("pinchsms.devices.claim_interface")
    @patch("pinchsms.devices.find_devices")
    def test_detects_generic(self, mock_find, mock_claim, mock_sleep):
        dev = MagicMock()
        dev.idVendor = 0x9999
        dev.idProduct = 0x1111
        mock_find.return_value = [dev]
        mock_claim.return_value = _mock_endpoints()

        _modem, quirks = detect_modem()
        assert isinstance(quirks, GenericQuirks)

    @patch("pinchsms.core.modem.time.sleep")
    @patch("pinchsms.devices.claim_interface")
    @patch("pinchsms.devices.find_devices")
    def test_filter_by_name(self, mock_find, mock_claim, mock_sleep):
        dev = MagicMock()
        dev.idVendor = 0x9999
        dev.idProduct = 0x1111
        mock_find.return_value = [dev]
        mock_claim.return_value = _mock_endpoints()

        _modem, quirks = detect_modem(device_name="Generic AT Modem")
        assert isinstance(quirks, GenericQuirks)

    @patch("pinchsms.devices.find_devices")
    def test_filter_no_match(self, mock_find):
        dev = MagicMock()
        dev.idVendor = 0x9999
        dev.idProduct = 0x1111
        mock_find.return_value = [dev]

        with pytest.raises(ModemError, match="No supported modem found"):
            detect_modem(device_name="NonExistent")


class TestListDevices:
    @patch("pinchsms.devices.find_devices", return_value=[])
    def test_empty(self, mock_find):
        assert list_devices() == []

    @patch("pinchsms.devices.find_devices")
    def test_lists_with_quirk_match(self, mock_find):
        dev = MagicMock()
        dev.idVendor = VENDOR_ID
        dev.idProduct = PRODUCT_MODEM
        mock_find.return_value = [dev]

        result = list_devices()
        assert len(result) == 1
        assert result[0]["device"] == "SEW132"
        assert result[0]["vendor_id"] == f"0x{VENDOR_ID:04X}"

    @patch("pinchsms.devices.find_devices")
    def test_generic_fallback(self, mock_find):
        dev = MagicMock()
        dev.idVendor = 0xAAAA
        dev.idProduct = 0xBBBB
        mock_find.return_value = [dev]

        result = list_devices()
        assert result[0]["device"] == "SEW132" or result[0]["device"] == "Generic AT Modem"
