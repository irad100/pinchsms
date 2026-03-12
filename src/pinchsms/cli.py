import argparse
import sys
import time
from datetime import datetime

import usb.core

from pinchsms.config import load_config
from pinchsms.core.modem import ModemError
from pinchsms.devices import detect_modem, list_devices
from pinchsms.forwarding import build_forwarders


def main() -> None:
    parser = argparse.ArgumentParser(prog="pinchsms", description="USB modem SMS tool")
    parser.add_argument("--config", "-c", help="Path to config file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    sub = parser.add_subparsers(dest="command")

    sub.add_parser("monitor", help="Monitor for incoming SMS")
    sub.add_parser("devices", help="List detected USB modems")

    send_p = sub.add_parser("send", help="Send an SMS")
    send_p.add_argument("number", help="Recipient phone number")
    send_p.add_argument("message", help="Message text")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    if args.command == "monitor":
        _cmd_monitor(args)
    elif args.command == "send":
        _cmd_send(args)
    elif args.command == "devices":
        _cmd_devices()


def _cmd_monitor(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    forwarders = build_forwarders(config)

    modem = None
    try:
        while True:
            if modem is None or not modem.connected:
                try:
                    _log("Connecting to modem...")
                    modem, quirks = detect_modem(config.modem.device)
                    _log(f"Connected to {quirks.name}. Monitoring for SMS.\n")
                except ModemError as e:
                    _log(f"Connection failed: {e}")
                    _log(f"Retrying in {config.modem.reconnect_delay}s...\n")
                    time.sleep(config.modem.reconnect_delay)
                    continue

            try:
                modem.check_notifications()
                messages = modem.read_sms()
                for msg in messages:
                    _log("NEW SMS")
                    print(f"  From: {msg.sender}")
                    print(f"  Date: {msg.timestamp}")
                    print(f"  Body: {msg.body}")

                    for fwd in forwarders:
                        try:
                            fwd.forward(msg)
                            if args.verbose:
                                _log(f"  Forwarded via {type(fwd).__name__}")
                        except Exception as e:
                            _log(f"  Forward failed ({type(fwd).__name__}): {e}")

                    if config.modem.delete_after_read:
                        modem.delete_sms(msg.index)
                        print("  (deleted from SIM)\n")

                time.sleep(config.modem.poll_interval)

            except (usb.core.USBError, ModemError) as e:
                _log(f"USB error: {e}")
                if modem:
                    modem.disconnect()
                _log(f"Reconnecting in {config.modem.reconnect_delay}s...\n")
                time.sleep(config.modem.reconnect_delay)

    except KeyboardInterrupt:
        _log("Stopped.")
    finally:
        if modem:
            modem.disconnect()


def _cmd_send(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    try:
        modem, quirks = detect_modem(config.modem.device)
        _log(f"Connected to {quirks.name}")
        response = modem.send_sms(args.number, args.message)
        if "OK" in response:
            _log(f"SMS sent to {args.number}")
        else:
            _log(f"Send may have failed. Modem response: {response.strip()}")
        modem.disconnect()
    except ModemError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def _cmd_devices() -> None:
    devices = list_devices()
    if not devices:
        print("No USB devices found.")
        return
    for dev in devices:
        print(f"  {dev['vendor_id']}:{dev['product_id']}  {dev['device']}")


def _log(msg: str) -> None:
    print(f"[{datetime.now():%H:%M:%S}] {msg}")


if __name__ == "__main__":  # pragma: no cover
    main()
