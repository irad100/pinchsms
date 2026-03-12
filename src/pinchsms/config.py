import tomllib
from pathlib import Path

from pydantic import BaseModel


class ModemConfig(BaseModel):
    device: str = "auto"
    poll_interval: float = 5.0
    reconnect_delay: float = 10.0
    delete_after_read: bool = True


class WebhookConfig(BaseModel):
    url: str = ""
    headers: dict[str, str] = {}


class MqttConfig(BaseModel):
    broker: str = ""
    port: int = 1883
    topic: str = "pinchsms/messages"
    username: str = ""
    password: str = ""


class PinchConfig(BaseModel):
    modem: ModemConfig = ModemConfig()
    webhook: WebhookConfig = WebhookConfig()
    mqtt: MqttConfig = MqttConfig()


_SEARCH_PATHS = [
    Path("pinchsms.toml"),
    Path.home() / ".config" / "pinchsms" / "config.toml",
]


def load_config(path: str | None = None) -> PinchConfig:
    """Load configuration from TOML file.

    Search order: explicit path -> ./pinchsms.toml -> ~/.config/pinchsms/config.toml -> defaults.
    """
    if path is not None:
        config_path = Path(path)
        if not config_path.exists():
            msg = f"Config file not found: {path}"
            raise FileNotFoundError(msg)
        return _parse_toml(config_path)

    for candidate in _SEARCH_PATHS:
        if candidate.exists():  # pragma: no cover — depends on filesystem state
            return _parse_toml(candidate)

    return PinchConfig()


def _parse_toml(path: Path) -> PinchConfig:
    with open(path, "rb") as f:
        data = tomllib.load(f)

    return PinchConfig(
        modem=ModemConfig(**data.get("modem", {})),
        webhook=WebhookConfig(**data.get("webhook", {})),
        mqtt=MqttConfig(**data.get("mqtt", {})),
    )
