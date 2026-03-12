import json
import urllib.request

from pydantic import BaseModel

from pinchsms.core.sms import SmsMessage


class WebhookForwarder(BaseModel):
    """Forward SMS messages via HTTP POST."""

    url: str
    headers: dict[str, str] = {}

    def forward(self, msg: SmsMessage) -> None:
        payload = json.dumps(
            {
                "index": msg.index,
                "sender": msg.sender,
                "timestamp": msg.timestamp,
                "body": msg.body,
            }
        ).encode()

        headers = {"Content-Type": "application/json", **self.headers}
        req = urllib.request.Request(self.url, data=payload, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            resp.read()
