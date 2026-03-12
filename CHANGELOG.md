# Changelog

## v0.1.0

Initial release.

- AT-command modem interface over USB bulk endpoints
- SMS monitoring with configurable polling
- SMS sending via `pinchsms send`
- Device quirks system (SEW132, Generic fallback)
- Webhook forwarding (HTTP POST, stdlib urllib)
- MQTT forwarding (optional paho-mqtt dependency)
- TOML configuration with search path resolution
- CLI: `monitor`, `send`, `devices` subcommands
