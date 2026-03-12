from unittest.mock import MagicMock, patch

import pytest
import usb.core
import usb.util

from pinchsms.core.usb import claim_interface, find_devices


class TestFindDevices:
    @patch("pinchsms.core.usb.usb.core.find")
    def test_returns_list(self, mock_find: MagicMock):
        dev1, dev2 = MagicMock(), MagicMock()
        mock_find.return_value = [dev1, dev2]

        result = find_devices()
        assert result == [dev1, dev2]
        mock_find.assert_called_once_with(find_all=True)

    @patch("pinchsms.core.usb.usb.core.find")
    def test_filter_by_vendor(self, mock_find: MagicMock):
        mock_find.return_value = []

        result = find_devices(vendor_id=0x1BBB)
        assert result == []
        mock_find.assert_called_once_with(find_all=True, idVendor=0x1BBB)

    @patch("pinchsms.core.usb.usb.core.find")
    def test_no_devices(self, mock_find: MagicMock):
        mock_find.return_value = []
        assert find_devices() == []


class TestClaimInterface:
    def _make_device_with_endpoints(self, has_out=True, has_in=True, kernel_active=False):
        dev = MagicMock()
        dev.is_kernel_driver_active.return_value = kernel_active

        endpoints = []
        if has_out:
            ep_out = MagicMock()
            ep_out.bEndpointAddress = 0x01
            ep_out.bmAttributes = usb.util.ENDPOINT_TYPE_BULK
            endpoints.append(ep_out)
        if has_in:
            ep_in = MagicMock()
            ep_in.bEndpointAddress = 0x81
            ep_in.bmAttributes = usb.util.ENDPOINT_TYPE_BULK
            endpoints.append(ep_in)

        intf = MagicMock()
        intf.__iter__ = MagicMock(return_value=iter(endpoints))

        cfg = MagicMock()
        cfg.__getitem__ = MagicMock(return_value=intf)
        dev.get_active_configuration.return_value = cfg

        return dev

    @patch("pinchsms.core.usb.usb.util.endpoint_type")
    @patch("pinchsms.core.usb.usb.util.endpoint_direction")
    @patch("pinchsms.core.usb.usb.util.claim_interface")
    def test_claims_and_returns_endpoints(self, mock_claim, mock_dir, mock_type):
        dev = self._make_device_with_endpoints()
        mock_dir.side_effect = [usb.util.ENDPOINT_OUT, usb.util.ENDPOINT_IN]
        mock_type.side_effect = [usb.util.ENDPOINT_TYPE_BULK, usb.util.ENDPOINT_TYPE_BULK]

        ep_out, ep_in = claim_interface(dev, 0)
        assert ep_out is not None
        assert ep_in is not None
        mock_claim.assert_called_once_with(dev, 0)

    @patch("pinchsms.core.usb.usb.util.endpoint_type")
    @patch("pinchsms.core.usb.usb.util.endpoint_direction")
    @patch("pinchsms.core.usb.usb.util.claim_interface")
    def test_detaches_kernel_driver(self, mock_claim, mock_dir, mock_type):
        dev = self._make_device_with_endpoints(kernel_active=True)
        mock_dir.side_effect = [usb.util.ENDPOINT_OUT, usb.util.ENDPOINT_IN]
        mock_type.side_effect = [usb.util.ENDPOINT_TYPE_BULK, usb.util.ENDPOINT_TYPE_BULK]

        claim_interface(dev, 3)
        dev.detach_kernel_driver.assert_called_once_with(3)

    @patch("pinchsms.core.usb.usb.util.endpoint_type")
    @patch("pinchsms.core.usb.usb.util.endpoint_direction")
    @patch("pinchsms.core.usb.usb.util.claim_interface")
    def test_kernel_driver_error_suppressed(self, mock_claim, mock_dir, mock_type):
        dev = self._make_device_with_endpoints()
        dev.is_kernel_driver_active.side_effect = usb.core.USBError("not supported")
        mock_dir.side_effect = [usb.util.ENDPOINT_OUT, usb.util.ENDPOINT_IN]
        mock_type.side_effect = [usb.util.ENDPOINT_TYPE_BULK, usb.util.ENDPOINT_TYPE_BULK]

        ep_out, _ep_in = claim_interface(dev, 0)
        assert ep_out is not None

    @patch("pinchsms.core.usb.usb.util.endpoint_type")
    @patch("pinchsms.core.usb.usb.util.endpoint_direction")
    @patch("pinchsms.core.usb.usb.util.claim_interface")
    def test_not_implemented_suppressed(self, mock_claim, mock_dir, mock_type):
        dev = self._make_device_with_endpoints()
        dev.is_kernel_driver_active.side_effect = NotImplementedError
        mock_dir.side_effect = [usb.util.ENDPOINT_OUT, usb.util.ENDPOINT_IN]
        mock_type.side_effect = [usb.util.ENDPOINT_TYPE_BULK, usb.util.ENDPOINT_TYPE_BULK]

        ep_out, _ep_in = claim_interface(dev, 0)
        assert ep_out is not None

    @patch("pinchsms.core.usb.usb.util.endpoint_type")
    @patch("pinchsms.core.usb.usb.util.endpoint_direction")
    @patch("pinchsms.core.usb.usb.util.claim_interface")
    def test_raises_when_no_out_endpoint(self, mock_claim, mock_dir, mock_type):
        dev = self._make_device_with_endpoints(has_out=False)
        mock_dir.side_effect = [usb.util.ENDPOINT_IN]
        mock_type.side_effect = [usb.util.ENDPOINT_TYPE_BULK]

        with pytest.raises(usb.core.USBError, match="No bulk endpoints"):
            claim_interface(dev, 0)

    @patch("pinchsms.core.usb.usb.util.endpoint_type")
    @patch("pinchsms.core.usb.usb.util.endpoint_direction")
    @patch("pinchsms.core.usb.usb.util.claim_interface")
    def test_raises_when_no_in_endpoint(self, mock_claim, mock_dir, mock_type):
        dev = self._make_device_with_endpoints(has_in=False)
        mock_dir.side_effect = [usb.util.ENDPOINT_OUT]
        mock_type.side_effect = [usb.util.ENDPOINT_TYPE_BULK]

        with pytest.raises(usb.core.USBError, match="No bulk endpoints"):
            claim_interface(dev, 0)

    @patch("pinchsms.core.usb.usb.util.endpoint_type")
    @patch("pinchsms.core.usb.usb.util.endpoint_direction")
    @patch("pinchsms.core.usb.usb.util.claim_interface")
    def test_skips_non_bulk_endpoints(self, mock_claim, mock_dir, mock_type):
        dev = self._make_device_with_endpoints()
        mock_dir.side_effect = [usb.util.ENDPOINT_OUT, usb.util.ENDPOINT_IN]
        mock_type.side_effect = [usb.util.ENDPOINT_TYPE_ISO, usb.util.ENDPOINT_TYPE_ISO]

        with pytest.raises(usb.core.USBError, match="No bulk endpoints"):
            claim_interface(dev, 0)
