from typing import TYPE_CHECKING

from pinchsms.forwarding.webhook import WebhookForwarder

if TYPE_CHECKING:
    from pinchsms.config import PinchConfig
    from pinchsms.forwarding.base import Forwarder


def build_forwarders(config: PinchConfig) -> list[Forwarder]:
    """Build a list of configured forwarders from the config."""
    forwarders: list[Forwarder] = []

    if config.webhook.url:
        forwarders.append(
            WebhookForwarder(
                url=config.webhook.url,
                headers=config.webhook.headers,
            )
        )

    if config.mqtt.broker:
        try:
            from pinchsms.forwarding.mqtt import MqttForwarder
        except ImportError as e:
            msg = "MQTT forwarding requires paho-mqtt: pip install pinchsms[mqtt]"
            raise ImportError(msg) from e
        forwarders.append(
            MqttForwarder(
                broker=config.mqtt.broker,
                port=config.mqtt.port,
                topic=config.mqtt.topic,
                username=config.mqtt.username,
                password=config.mqtt.password,
            )
        )

    return forwarders
