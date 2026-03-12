import os
import tempfile

import pytest

from pinchsms.config import PinchConfig, load_config


class TestLoadConfig:
    def test_defaults(self):
        config = load_config()
        assert config.modem.device == "auto"
        assert config.modem.poll_interval == 5.0
        assert config.webhook.url == ""
        assert config.mqtt.broker == ""

    def test_load_from_file(self):
        toml_content = b"""
[modem]
device = "SEW132"
poll_interval = 10.0
delete_after_read = false

[webhook]
url = "https://example.com/hook"

[mqtt]
broker = "mqtt.example.com"
port = 8883
topic = "sms/inbox"
"""
        with tempfile.NamedTemporaryFile(suffix=".toml", delete=False) as f:
            f.write(toml_content)
            f.flush()
            try:
                config = load_config(f.name)
                assert config.modem.device == "SEW132"
                assert config.modem.poll_interval == 10.0
                assert config.modem.delete_after_read is False
                assert config.webhook.url == "https://example.com/hook"
                assert config.mqtt.broker == "mqtt.example.com"
                assert config.mqtt.port == 8883
                assert config.mqtt.topic == "sms/inbox"
            finally:
                os.unlink(f.name)

    def test_missing_file_raises(self):
        with pytest.raises(FileNotFoundError):
            load_config("/nonexistent/config.toml")

    def test_partial_config(self):
        toml_content = b"""
[modem]
device = "custom"
"""
        with tempfile.NamedTemporaryFile(suffix=".toml", delete=False) as f:
            f.write(toml_content)
            f.flush()
            try:
                config = load_config(f.name)
                assert config.modem.device == "custom"
                assert config.modem.poll_interval == 5.0
                assert config.webhook.url == ""
            finally:
                os.unlink(f.name)

    def test_webhook_headers(self):
        toml_content = b"""
[webhook]
url = "https://example.com/hook"
headers = { Authorization = "Bearer token123" }
"""
        with tempfile.NamedTemporaryFile(suffix=".toml", delete=False) as f:
            f.write(toml_content)
            f.flush()
            try:
                config = load_config(f.name)
                assert config.webhook.headers["Authorization"] == "Bearer token123"
            finally:
                os.unlink(f.name)

    def test_default_config_is_valid(self):
        config = PinchConfig()
        assert config.modem.reconnect_delay == 10.0
        assert config.mqtt.port == 1883
        assert config.mqtt.topic == "pinchsms/messages"
