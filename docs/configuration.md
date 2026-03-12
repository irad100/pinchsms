# Configuration Reference

pinchsms uses TOML configuration. Config file search order:

1. `--config` CLI flag (explicit path)
2. `./pinchsms.toml` (current directory)
3. `~/.config/pinchsms/config.toml` (user config)
4. Built-in defaults

## Full Example

```toml
[modem]
device = "auto"           # "auto" | "SEW132" | "Generic AT Modem"
poll_interval = 5.0       # seconds between SMS checks
reconnect_delay = 10.0    # seconds before reconnect after USB error
delete_after_read = true  # delete SMS from SIM after reading

[webhook]
url = ""                  # HTTP POST endpoint (empty = disabled)
headers = {}              # extra headers, e.g. { Authorization = "Bearer token" }

[mqtt]
broker = ""               # MQTT broker hostname (empty = disabled)
port = 1883               # MQTT broker port
topic = "pinchsms/messages"  # MQTT topic
username = ""             # MQTT auth (optional)
password = ""             # MQTT auth (optional)
```

## Sections

### `[modem]`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `device` | string | `"auto"` | Device name filter or `"auto"` for auto-detect |
| `poll_interval` | float | `5.0` | Seconds between SMS polling cycles |
| `reconnect_delay` | float | `10.0` | Seconds to wait before reconnection attempt |
| `delete_after_read` | bool | `true` | Delete SMS from SIM after reading |

### `[webhook]`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `url` | string | `""` | Webhook URL. Empty disables webhook forwarding |
| `headers` | table | `{}` | Extra HTTP headers to include in POST |

Webhook payload (JSON):
```json
{
  "index": 1,
  "sender": "+1234567890",
  "timestamp": "26/03/10,14:30:00+00",
  "body": "Message text"
}
```

### `[mqtt]`

Requires `pip install pinchsms[mqtt]`.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `broker` | string | `""` | MQTT broker hostname. Empty disables MQTT |
| `port` | int | `1883` | MQTT broker port |
| `topic` | string | `"pinchsms/messages"` | MQTT publish topic |
| `username` | string | `""` | MQTT authentication username |
| `password` | string | `""` | MQTT authentication password |
