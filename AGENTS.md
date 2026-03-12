# pinchsms - Agent Instructions

## Project Overview

Universal AT-command USB modem SMS tool. Monitors for incoming SMS via USB modems and forwards via webhooks/MQTT.

## Structure

```
src/pinchsms/
  cli.py          - argparse CLI: monitor, send, devices
  config.py       - TOML config loading with dataclasses
  core/
    modem.py      - ATModem class (AT commands over USB bulk endpoints)
    sms.py        - SmsMessage dataclass + AT+CMGL parser
    usb.py        - USB device discovery + interface claiming
  devices/
    __init__.py   - REGISTRY, detect_modem(), list_devices()
    base.py       - DeviceQuirks Protocol
    sew132.py     - SEW132 mode-switch quirks
    generic.py    - Fallback for standard AT modems
  forwarding/
    __init__.py   - build_forwarders() factory
    base.py       - Forwarder Protocol
    webhook.py    - HTTP POST via urllib
    mqtt.py       - paho-mqtt (optional dep)
tests/            - pytest, mirrors src/ structure
```

## Dev Setup

```bash
uv sync --all-extras --group dev
```

## Commands

```bash
uv run ruff check --fix && uv run ruff format   # lint + format
uv run ty check                                   # type check
uv run pytest -q --cov=pinchsms                  # test
uv run pinchsms --help                            # CLI
```

## Adding Modem Support

1. Create `src/pinchsms/devices/yourmodem.py` implementing `DeviceQuirks` protocol
2. Add to `REGISTRY` in `src/pinchsms/devices/__init__.py` (before `GenericQuirks`)
3. Add tests in `tests/test_devices.py`

## Conventions

- src-layout, Python 3.14+
- Protocol-based (structural subtyping, no ABC)
- Synchronous (USB polling is blocking)
- stdlib only for HTTP (urllib.request)
- Optional deps via extras (`pinchsms[mqtt]`)
