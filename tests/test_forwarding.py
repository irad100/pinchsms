import json
from unittest.mock import MagicMock, patch

import pytest

from pinchsms.config import MqttConfig, PinchConfig, WebhookConfig
from pinchsms.core.sms import SmsMessage
from pinchsms.forwarding import build_forwarders
from pinchsms.forwarding.webhook import WebhookForwarder


def _make_msg() -> SmsMessage:
    return SmsMessage(index=1, sender="+1234", timestamp="26/03/10,14:30:00+00", body="Hello")


class TestWebhookForwarder:
    @patch("pinchsms.forwarding.webhook.urllib.request.urlopen")
    def test_forward_sends_post(self, mock_urlopen: MagicMock):
        mock_resp = MagicMock()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        fwd = WebhookForwarder(url="https://example.com/hook")
        fwd.forward(_make_msg())

        mock_urlopen.assert_called_once()
        req = mock_urlopen.call_args[0][0]
        assert req.full_url == "https://example.com/hook"
        assert req.method == "POST"
        payload = json.loads(req.data)
        assert payload["sender"] == "+1234"
        assert payload["body"] == "Hello"

    @patch("pinchsms.forwarding.webhook.urllib.request.urlopen")
    def test_forward_custom_headers(self, mock_urlopen: MagicMock):
        mock_resp = MagicMock()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        fwd = WebhookForwarder(
            url="https://example.com/hook",
            headers={"Authorization": "Bearer abc"},
        )
        fwd.forward(_make_msg())

        req = mock_urlopen.call_args[0][0]
        assert req.get_header("Authorization") == "Bearer abc"


class TestBuildForwarders:
    def test_no_forwarders_by_default(self):
        config = PinchConfig()
        fwds = build_forwarders(config)
        assert fwds == []

    def test_webhook_forwarder_created(self):
        config = PinchConfig(webhook=WebhookConfig(url="https://example.com/hook"))
        fwds = build_forwarders(config)
        assert len(fwds) == 1
        assert isinstance(fwds[0], WebhookForwarder)

    def test_mqtt_forwarder_created(self):
        config = PinchConfig(mqtt=MqttConfig(broker="mqtt.example.com"))
        fwds = build_forwarders(config)
        assert len(fwds) == 1

        from pinchsms.forwarding.mqtt import MqttForwarder

        assert isinstance(fwds[0], MqttForwarder)

    def test_both_forwarders(self):
        config = PinchConfig(
            webhook=WebhookConfig(url="https://example.com/hook"),
            mqtt=MqttConfig(broker="mqtt.example.com"),
        )
        fwds = build_forwarders(config)
        assert len(fwds) == 2

    def test_mqtt_import_error(self):
        config = PinchConfig(mqtt=MqttConfig(broker="mqtt.example.com"))
        blocked = {
            "paho": None,
            "paho.mqtt": None,
            "paho.mqtt.client": None,
            "pinchsms.forwarding.mqtt": None,
        }
        with (
            patch.dict("sys.modules", blocked),
            pytest.raises(ImportError, match="paho-mqtt"),
        ):
            build_forwarders(config)


class TestMqttForwarder:
    @patch("pinchsms.forwarding.mqtt.mqtt_client")
    def test_forward_publishes(self, mock_mqtt_mod: MagicMock):
        mock_client = MagicMock()
        mock_mqtt_mod.Client.return_value = mock_client

        from pinchsms.forwarding.mqtt import MqttForwarder

        fwd = MqttForwarder(broker="localhost", port=1883, topic="test/sms")
        fwd.forward(_make_msg())

        mock_mqtt_mod.Client.assert_called_once()
        mock_client.connect.assert_called_once_with("localhost", 1883)
        mock_client.publish.assert_called_once()
        payload = json.loads(mock_client.publish.call_args[0][1])
        assert payload["sender"] == "+1234"
        assert mock_client.publish.call_args[0][0] == "test/sms"
        mock_client.disconnect.assert_called_once()

    @patch("pinchsms.forwarding.mqtt.mqtt_client")
    def test_forward_with_auth(self, mock_mqtt_mod: MagicMock):
        mock_client = MagicMock()
        mock_mqtt_mod.Client.return_value = mock_client

        from pinchsms.forwarding.mqtt import MqttForwarder

        fwd = MqttForwarder(broker="localhost", username="user", password="pass")
        fwd.forward(_make_msg())

        mock_client.username_pw_set.assert_called_once_with("user", "pass")

    @patch("pinchsms.forwarding.mqtt.mqtt_client")
    def test_forward_no_auth(self, mock_mqtt_mod: MagicMock):
        mock_client = MagicMock()
        mock_mqtt_mod.Client.return_value = mock_client

        from pinchsms.forwarding.mqtt import MqttForwarder

        fwd = MqttForwarder(broker="localhost")
        fwd.forward(_make_msg())

        mock_client.username_pw_set.assert_not_called()
