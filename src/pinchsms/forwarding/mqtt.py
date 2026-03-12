import json

import paho.mqtt.client as mqtt_client
from pydantic import BaseModel

from pinchsms.core.sms import SmsMessage


class MqttForwarder(BaseModel):
    """Forward SMS messages via MQTT."""

    broker: str
    port: int = 1883
    topic: str = "pinchsms/messages"
    username: str = ""
    password: str = ""

    def forward(self, msg: SmsMessage) -> None:
        payload = json.dumps(
            {
                "index": msg.index,
                "sender": msg.sender,
                "timestamp": msg.timestamp,
                "body": msg.body,
            }
        )

        client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION2)
        if self.username:
            client.username_pw_set(self.username, self.password)
        client.connect(self.broker, self.port)
        client.publish(self.topic, payload)
        client.disconnect()
