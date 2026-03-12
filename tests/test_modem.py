from unittest.mock import MagicMock, patch

import usb.core

from pinchsms.core.modem import ATModem, ModemError


def _make_modem():
    dev = MagicMock()
    ep_out = MagicMock()
    ep_in = MagicMock()
    return ATModem(dev, ep_out, ep_in), dev, ep_out, ep_in


class TestATModemInit:
    def test_stores_endpoints(self):
        modem, dev, ep_out, ep_in = _make_modem()
        assert modem.dev is dev
        assert modem.ep_out is ep_out
        assert modem.ep_in is ep_in

    def test_connected_true(self):
        modem, *_ = _make_modem()
        assert modem.connected is True

    def test_connected_false_after_disconnect(self):
        modem, *_ = _make_modem()
        modem.disconnect()
        assert modem.connected is False


class TestSendAt:
    @patch("pinchsms.core.modem.time.sleep")
    def test_sends_command_and_reads(self, mock_sleep: MagicMock):
        modem, _, ep_out, ep_in = _make_modem()
        ep_in.read.side_effect = [b"OK\r\n", usb.core.USBTimeoutError("timeout")]

        result = modem.send_at("AT")

        ep_out.write.assert_called_once_with(b"AT\r\n")
        mock_sleep.assert_called_once_with(1.0)
        assert "OK" in result

    @patch("pinchsms.core.modem.time.sleep")
    def test_custom_wait(self, mock_sleep: MagicMock):
        modem, _, _, ep_in = _make_modem()
        ep_in.read.side_effect = usb.core.USBTimeoutError("timeout")

        modem.send_at("AT", wait=2.5)
        mock_sleep.assert_called_once_with(2.5)


class TestReadResponse:
    def test_reads_multiple_chunks(self):
        modem, _, _, ep_in = _make_modem()
        ep_in.read.side_effect = [b"Hello ", b"World", usb.core.USBTimeoutError("timeout")]

        result = modem._read_response()
        assert result == "Hello World"

    def test_empty_on_immediate_timeout(self):
        modem, _, _, ep_in = _make_modem()
        ep_in.read.side_effect = usb.core.USBTimeoutError("timeout")

        result = modem._read_response()
        assert result == ""

    def test_handles_invalid_utf8(self):
        modem, _, _, ep_in = _make_modem()
        ep_in.read.side_effect = [b"\xff\xfe", usb.core.USBTimeoutError("timeout")]

        result = modem._read_response()
        assert isinstance(result, str)


class TestDrain:
    def test_calls_read_response(self):
        modem, _, _, ep_in = _make_modem()
        ep_in.read.side_effect = usb.core.USBTimeoutError("timeout")

        modem.drain()
        ep_in.read.assert_called_once_with(512, timeout=100)


class TestReadSms:
    @patch("pinchsms.core.modem.time.sleep")
    def test_parses_messages(self, mock_sleep: MagicMock):
        modem, _, _, ep_in = _make_modem()
        raw = '+CMGL: 1,"REC READ","+555","","26/01/01,00:00:00+00"\r\nHi\r\nOK\r\n'
        ep_in.read.side_effect = [raw.encode(), usb.core.USBTimeoutError("timeout")]

        msgs = modem.read_sms()
        assert len(msgs) == 1
        assert msgs[0].sender == "+555"
        assert msgs[0].body == "Hi"


class TestDeleteSms:
    @patch("pinchsms.core.modem.time.sleep")
    def test_sends_cmgd(self, mock_sleep: MagicMock):
        modem, _, ep_out, ep_in = _make_modem()
        ep_in.read.side_effect = usb.core.USBTimeoutError("timeout")

        modem.delete_sms(3)
        ep_out.write.assert_called_once_with(b"AT+CMGD=3\r\n")


class TestSendSms:
    @patch("pinchsms.core.modem.time.sleep")
    def test_sends_message_with_ctrl_z(self, mock_sleep: MagicMock):
        modem, _, ep_out, ep_in = _make_modem()
        ep_in.read.side_effect = [
            usb.core.USBTimeoutError("timeout"),  # _read_response after AT+CMGS
            b"+CMGS: 1\r\nOK\r\n",  # _read_response after text+ctrl-z
            usb.core.USBTimeoutError("timeout"),
        ]

        result = modem.send_sms("+1234", "Hello")

        calls = ep_out.write.call_args_list
        assert calls[0][0][0] == b'AT+CMGS="+1234"\r\n'
        assert calls[1][0][0] == b"Hello\x1a"
        assert "OK" in result


class TestCheckNotifications:
    def test_returns_true_on_cmti(self):
        modem, _, _, ep_in = _make_modem()
        ep_in.read.side_effect = [b'+CMTI: "SM",1\r\n', usb.core.USBTimeoutError("timeout")]

        assert modem.check_notifications() is True

    def test_returns_false_on_empty(self):
        modem, _, _, ep_in = _make_modem()
        ep_in.read.side_effect = usb.core.USBTimeoutError("timeout")

        assert modem.check_notifications() is False


class TestDisconnect:
    def test_releases_interface(self):
        modem, dev, _, _ = _make_modem()
        with patch("pinchsms.core.modem.usb.util.release_interface") as mock_release:
            modem.disconnect()
            mock_release.assert_called_once_with(dev, 0)

        assert modem.dev is None
        assert modem.ep_out is None
        assert modem.ep_in is None

    def test_noop_when_already_disconnected(self):
        modem, _, _, _ = _make_modem()
        modem.dev = None
        modem.disconnect()

    def test_suppresses_release_error(self):
        modem, _, _, _ = _make_modem()
        with patch("pinchsms.core.modem.usb.util.release_interface", side_effect=Exception("fail")):
            modem.disconnect()
        assert modem.dev is None


class TestModemError:
    def test_is_exception(self):
        assert issubclass(ModemError, Exception)

    def test_message(self):
        err = ModemError("test error")
        assert str(err) == "test error"
