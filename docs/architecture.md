# Architecture

## Data Flow

```
USB Bus
  |
  v
find_devices()          -- core/usb.py: enumerate USB devices
  |
  v
DeviceQuirks.matches()  -- devices/: match device to quirks handler
  |
  v
DeviceQuirks.prepare()  -- mode-switch if needed (e.g. SEW132 CD-ROM eject)
  |
  v
claim_interface()       -- core/usb.py: detach kernel driver, claim, find endpoints
  |
  v
ATModem                 -- core/modem.py: send AT commands, read responses
  |
  v
parse_message_listing() -- core/sms.py: AT+CMGL response -> SmsMessage list
  |
  v
Forwarder.forward()     -- forwarding/: webhook POST or MQTT publish
```

## Components

### Core (`core/`)

- **sms.py**: `SmsMessage` frozen dataclass and AT+CMGL parser
- **usb.py**: USB device discovery and interface claiming via pyusb
- **modem.py**: `ATModem` class wrapping AT command send/receive over bulk endpoints

### Devices (`devices/`)

Protocol-based quirks system. Each device type implements `DeviceQuirks`:
- `matches()` — device identification
- `prepare()` — hardware-specific setup (mode-switching)
- `get_interface()` — which USB interface to claim
- `post_connect()` — AT init commands after connection

Registry in `__init__.py` tries quirks in order; `GenericQuirks` is the fallback.

### Forwarding (`forwarding/`)

Protocol-based forwarders. `build_forwarders()` reads config and instantiates active forwarders.
- **WebhookForwarder**: HTTP POST with JSON payload via `urllib.request`
- **MqttForwarder**: MQTT publish via `paho-mqtt` (optional dependency)

### Config (`config.py`)

TOML-based configuration using `tomllib`. Dataclasses for type safety.
Search order: `--config` flag, `./pinchsms.toml`, `~/.config/pinchsms/config.toml`, defaults.

### CLI (`cli.py`)

argparse with subcommands: `monitor`, `send`, `devices`.
