<p align="center">
  <img src="logo.svg" alt="pinchsms logo" width="200">
</p>

<h1 align="center">pinchsms</h1>

<p align="center">
  Universal AT-command USB modem SMS tool with webhook/MQTT forwarding.
</p>

<p align="center">
  <a href="https://pypi.org/project/pinchsms/"><img src="https://img.shields.io/pypi/v/pinchsms" alt="PyPI"></a>
  <a href="https://pypi.org/project/pinchsms/"><img src="https://img.shields.io/pypi/pyversions/pinchsms" alt="Python"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/openclaw/pinchsms" alt="License"></a>
</p>

---

**pinchsms** monitors USB modems for incoming SMS and forwards them via webhooks or MQTT. It supports any AT-command modem with a device quirks system for hardware-specific behavior.

Part of the [OpenClaw](https://github.com/openclaw) ecosystem.

## Install

```bash
pip install pinchsms

# With MQTT support
pip install pinchsms[mqtt]
```

Requires Python 3.14+ and [libusb](https://libusb.info/).

## Quick Start

```bash
# List detected USB modems
pinchsms devices

# Monitor for incoming SMS (prints to stdout)
pinchsms monitor

# Send an SMS
pinchsms send "+1234567890" "Hello from pinchsms"
```

## Configuration

Create `pinchsms.toml` in the current directory or `~/.config/pinchsms/config.toml`:

```toml
[modem]
device = "auto"           # "auto", "SEW132", or "Generic AT Modem"
poll_interval = 5.0       # seconds between SMS checks
reconnect_delay = 10.0    # seconds before reconnect attempt
delete_after_read = true  # remove SMS from SIM after reading

[webhook]
url = "https://example.com/sms"
headers = { Authorization = "Bearer your-token" }

[mqtt]
broker = "mqtt.example.com"
port = 1883
topic = "pinchsms/messages"
username = ""
password = ""
```

## Supported Modems

| Device | Vendor ID | Status |
|--------|-----------|--------|
| Strong Rising SEW132 | 0x1BBB | Full support (auto mode-switch) |
| Generic AT modem | any | Basic support |

See [Adding Modem Support](docs/adding-modems.md) to add your own.

## Architecture

```
USB Device -> DeviceQuirks -> ATModem -> SmsMessage -> Forwarder(s)
                                  \-> CLI output
```

See [docs/architecture.md](docs/architecture.md) for details.

## Development

```bash
git clone https://github.com/openclaw/pinchsms
cd pinchsms
uv sync --all-extras --group dev
uv run ruff check
uv run pytest -q
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for full guidelines.

## License

[MIT](LICENSE)
