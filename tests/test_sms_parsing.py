import pytest
from pydantic import ValidationError

from pinchsms.core.sms import SmsMessage, parse_message_listing


class TestParseMessageListing:
    def test_single_message(self):
        raw = '+CMGL: 1,"REC READ","+1234567890","","26/03/10,14:30:00+00"\r\nHello world\r\nOK\r\n'
        msgs = parse_message_listing(raw)
        assert len(msgs) == 1
        assert msgs[0] == SmsMessage(
            index=1,
            sender="+1234567890",
            timestamp="26/03/10,14:30:00+00",
            body="Hello world",
        )

    def test_multiple_messages(self):
        raw = (
            '+CMGL: 0,"REC READ","+111","","26/01/01,00:00:00+00"\r\n'
            "First\r\n"
            '+CMGL: 1,"REC READ","+222","","26/01/02,00:00:00+00"\r\n'
            "Second\r\n"
            "OK\r\n"
        )
        msgs = parse_message_listing(raw)
        assert len(msgs) == 2
        assert msgs[0].sender == "+111"
        assert msgs[0].body == "First"
        assert msgs[1].sender == "+222"
        assert msgs[1].body == "Second"

    def test_multiline_body(self):
        raw = (
            '+CMGL: 5,"REC READ","+999","","26/03/10,10:00:00+00"\r\nLine one\r\nLine two\r\nOK\r\n'
        )
        msgs = parse_message_listing(raw)
        assert len(msgs) == 1
        assert msgs[0].body == "Line one\nLine two"

    def test_empty_response(self):
        assert parse_message_listing("") == []
        assert parse_message_listing("OK") == []

    def test_no_messages(self):
        raw = "\r\nOK\r\n"
        assert parse_message_listing(raw) == []

    def test_index_parsing(self):
        raw = '+CMGL: 42,"REC READ","+555","","26/06/15,12:00:00+00"\r\nTest\r\nOK\r\n'
        msgs = parse_message_listing(raw)
        assert msgs[0].index == 42

    def test_frozen_model(self):
        msg = SmsMessage(index=0, sender="+1", timestamp="now", body="hi")
        with pytest.raises(ValidationError, match="frozen"):
            msg.body = "changed"  # type: ignore[misc]
