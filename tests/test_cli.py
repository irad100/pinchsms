import argparse
from unittest.mock import MagicMock, patch

from pinchsms.cli import _cmd_devices, _cmd_monitor, _cmd_send, main
from pinchsms.core.modem import ModemError
from pinchsms.core.sms import SmsMessage


class TestMain:
    @patch("pinchsms.cli.sys.exit")
    def test_no_command_exits(self, mock_exit: MagicMock, capsys):
        with patch("pinchsms.cli.argparse.ArgumentParser.parse_args") as mock_parse:
            mock_parse.return_value = argparse.Namespace(command=None, config=None, verbose=False)
            main()
            mock_exit.assert_called_once_with(1)

    @patch("pinchsms.cli._cmd_monitor")
    def test_routes_monitor(self, mock_monitor: MagicMock):
        with patch("pinchsms.cli.argparse.ArgumentParser.parse_args") as mock_parse:
            mock_parse.return_value = argparse.Namespace(
                command="monitor", config=None, verbose=False
            )
            main()
            mock_monitor.assert_called_once()

    @patch("pinchsms.cli._cmd_send")
    def test_routes_send(self, mock_send: MagicMock):
        with patch("pinchsms.cli.argparse.ArgumentParser.parse_args") as mock_parse:
            mock_parse.return_value = argparse.Namespace(
                command="send", config=None, verbose=False, number="+1", message="hi"
            )
            main()
            mock_send.assert_called_once()

    @patch("pinchsms.cli._cmd_devices")
    def test_routes_devices(self, mock_devices: MagicMock):
        with patch("pinchsms.cli.argparse.ArgumentParser.parse_args") as mock_parse:
            mock_parse.return_value = argparse.Namespace(
                command="devices", config=None, verbose=False
            )
            main()
            mock_devices.assert_called_once()


class TestCmdDevices:
    @patch("pinchsms.cli.list_devices")
    def test_no_devices(self, mock_list: MagicMock, capsys):
        mock_list.return_value = []
        _cmd_devices()
        assert "No USB devices found" in capsys.readouterr().out

    @patch("pinchsms.cli.list_devices")
    def test_lists_devices(self, mock_list: MagicMock, capsys):
        mock_list.return_value = [
            {"vendor_id": "0x1BBB", "product_id": "0x011E", "device": "SEW132"}
        ]
        _cmd_devices()
        out = capsys.readouterr().out
        assert "0x1BBB" in out
        assert "SEW132" in out


class TestCmdSend:
    @patch("pinchsms.cli.detect_modem")
    @patch("pinchsms.cli.load_config")
    def test_send_success(self, mock_config, mock_detect, capsys):
        from pinchsms.config import PinchConfig

        mock_config.return_value = PinchConfig()
        mock_modem = MagicMock()
        mock_quirks = MagicMock()
        mock_quirks.name = "TestModem"
        mock_modem.send_sms.return_value = "OK\r\n"
        mock_detect.return_value = (mock_modem, mock_quirks)

        args = argparse.Namespace(config=None, verbose=False, number="+1234", message="Hello")
        _cmd_send(args)

        mock_modem.send_sms.assert_called_once_with("+1234", "Hello")
        mock_modem.disconnect.assert_called_once()
        out = capsys.readouterr().out
        assert "SMS sent" in out

    @patch("pinchsms.cli.detect_modem")
    @patch("pinchsms.cli.load_config")
    def test_send_failure_response(self, mock_config, mock_detect, capsys):
        from pinchsms.config import PinchConfig

        mock_config.return_value = PinchConfig()
        mock_modem = MagicMock()
        mock_quirks = MagicMock()
        mock_quirks.name = "TestModem"
        mock_modem.send_sms.return_value = "ERROR\r\n"
        mock_detect.return_value = (mock_modem, mock_quirks)

        args = argparse.Namespace(config=None, verbose=False, number="+1234", message="Hello")
        _cmd_send(args)

        out = capsys.readouterr().out
        assert "may have failed" in out

    @patch("pinchsms.cli.sys.exit")
    @patch("pinchsms.cli.detect_modem", side_effect=ModemError("No modem"))
    @patch("pinchsms.cli.load_config")
    def test_send_modem_error(self, mock_config, mock_detect, mock_exit, capsys):
        from pinchsms.config import PinchConfig

        mock_config.return_value = PinchConfig()

        args = argparse.Namespace(config=None, verbose=False, number="+1234", message="Hello")
        _cmd_send(args)

        mock_exit.assert_called_once_with(1)
        err = capsys.readouterr().err
        assert "No modem" in err


class TestCmdMonitor:
    @patch("pinchsms.cli.time.sleep")
    @patch("pinchsms.cli.detect_modem")
    @patch("pinchsms.cli.build_forwarders")
    @patch("pinchsms.cli.load_config")
    def test_monitor_receives_and_deletes(self, mock_config, mock_fwd, mock_detect, mock_sleep):
        from pinchsms.config import PinchConfig

        mock_config.return_value = PinchConfig()
        mock_fwd.return_value = []

        mock_modem = MagicMock()
        mock_quirks = MagicMock()
        mock_quirks.name = "TestModem"
        mock_modem.connected = True
        mock_modem.check_notifications.return_value = False
        msg = SmsMessage(index=1, sender="+555", timestamp="now", body="Test")
        mock_modem.read_sms.side_effect = [[msg], KeyboardInterrupt]
        mock_detect.return_value = (mock_modem, mock_quirks)

        args = argparse.Namespace(config=None, verbose=False)
        _cmd_monitor(args)

        mock_modem.delete_sms.assert_called_once_with(1)
        mock_modem.disconnect.assert_called()

    @patch("pinchsms.cli.time.sleep")
    @patch("pinchsms.cli.detect_modem", side_effect=[ModemError("fail"), KeyboardInterrupt])
    @patch("pinchsms.cli.build_forwarders")
    @patch("pinchsms.cli.load_config")
    def test_monitor_connection_retry(self, mock_config, mock_fwd, mock_detect, mock_sleep, capsys):
        from pinchsms.config import PinchConfig

        mock_config.return_value = PinchConfig()
        mock_fwd.return_value = []

        args = argparse.Namespace(config=None, verbose=False)
        _cmd_monitor(args)

        out = capsys.readouterr().out
        assert "Connection failed" in out
        assert "Retrying" in out

    @patch("pinchsms.cli.time.sleep")
    @patch("pinchsms.cli.detect_modem")
    @patch("pinchsms.cli.build_forwarders")
    @patch("pinchsms.cli.load_config")
    def test_monitor_usb_error_reconnects(
        self, mock_config, mock_fwd, mock_detect, mock_sleep, capsys
    ):
        import usb.core

        from pinchsms.config import PinchConfig

        mock_config.return_value = PinchConfig()
        mock_fwd.return_value = []

        mock_modem = MagicMock()
        mock_quirks = MagicMock()
        mock_quirks.name = "TestModem"
        mock_modem.connected = True
        mock_modem.check_notifications.side_effect = [
            usb.core.USBError("disconnected"),
            KeyboardInterrupt,
        ]
        mock_detect.return_value = (mock_modem, mock_quirks)

        args = argparse.Namespace(config=None, verbose=False)
        _cmd_monitor(args)

        out = capsys.readouterr().out
        assert "USB error" in out
        mock_modem.disconnect.assert_called()

    @patch("pinchsms.cli.time.sleep")
    @patch("pinchsms.cli.detect_modem")
    @patch("pinchsms.cli.build_forwarders")
    @patch("pinchsms.cli.load_config")
    def test_monitor_forwards_and_logs_verbose(
        self, mock_config, mock_fwd, mock_detect, mock_sleep, capsys
    ):
        from pinchsms.config import PinchConfig

        mock_config.return_value = PinchConfig()

        mock_forwarder = MagicMock()
        mock_fwd.return_value = [mock_forwarder]

        mock_modem = MagicMock()
        mock_quirks = MagicMock()
        mock_quirks.name = "TestModem"
        mock_modem.connected = True
        mock_modem.check_notifications.return_value = False
        msg = SmsMessage(index=1, sender="+555", timestamp="now", body="Test")
        mock_modem.read_sms.side_effect = [[msg], KeyboardInterrupt]
        mock_detect.return_value = (mock_modem, mock_quirks)

        args = argparse.Namespace(config=None, verbose=True)
        _cmd_monitor(args)

        mock_forwarder.forward.assert_called_once_with(msg)
        out = capsys.readouterr().out
        assert "Forwarded via" in out

    @patch("pinchsms.cli.time.sleep")
    @patch("pinchsms.cli.detect_modem")
    @patch("pinchsms.cli.build_forwarders")
    @patch("pinchsms.cli.load_config")
    def test_monitor_forward_error_logged(
        self, mock_config, mock_fwd, mock_detect, mock_sleep, capsys
    ):
        from pinchsms.config import PinchConfig

        mock_config.return_value = PinchConfig()

        mock_forwarder = MagicMock()
        mock_forwarder.forward.side_effect = Exception("webhook down")
        mock_fwd.return_value = [mock_forwarder]

        mock_modem = MagicMock()
        mock_quirks = MagicMock()
        mock_quirks.name = "TestModem"
        mock_modem.connected = True
        mock_modem.check_notifications.return_value = False
        msg = SmsMessage(index=1, sender="+555", timestamp="now", body="Test")
        mock_modem.read_sms.side_effect = [[msg], KeyboardInterrupt]
        mock_detect.return_value = (mock_modem, mock_quirks)

        args = argparse.Namespace(config=None, verbose=False)
        _cmd_monitor(args)

        out = capsys.readouterr().out
        assert "Forward failed" in out
        assert "webhook down" in out
