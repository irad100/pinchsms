from typing import TYPE_CHECKING

import usb.core
import usb.util

if TYPE_CHECKING:
    from usb.core import Device, Endpoint


def find_devices(vendor_id: int | None = None) -> list[Device]:
    """Find all USB devices, optionally filtered by vendor ID."""
    kwargs = {}
    if vendor_id is not None:
        kwargs["idVendor"] = vendor_id
    devices = usb.core.find(find_all=True, **kwargs)
    return list(devices)


def claim_interface(dev: Device, intf_num: int) -> tuple[Endpoint, Endpoint]:
    """Detach kernel driver, claim interface, return (ep_out, ep_in) bulk endpoints."""
    try:
        if dev.is_kernel_driver_active(intf_num):
            dev.detach_kernel_driver(intf_num)
    except usb.core.USBError, NotImplementedError:
        pass

    usb.util.claim_interface(dev, intf_num)
    cfg = dev.get_active_configuration()
    intf = cfg[(intf_num, 0)]

    ep_out = None
    ep_in = None
    for ep in intf:
        direction = usb.util.endpoint_direction(ep.bEndpointAddress)
        ep_type = usb.util.endpoint_type(ep.bmAttributes)
        if direction == usb.util.ENDPOINT_OUT and ep_type == usb.util.ENDPOINT_TYPE_BULK:
            ep_out = ep
        elif direction == usb.util.ENDPOINT_IN and ep_type == usb.util.ENDPOINT_TYPE_BULK:
            ep_in = ep

    if ep_out is None or ep_in is None:
        msg = f"No bulk endpoints found on interface {intf_num}"
        raise usb.core.USBError(msg)

    return ep_out, ep_in
