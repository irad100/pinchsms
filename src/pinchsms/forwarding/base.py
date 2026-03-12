from typing import Protocol  # pragma: no cover

from pinchsms.core.sms import SmsMessage  # pragma: no cover


class Forwarder(Protocol):  # pragma: no cover
    """Protocol for SMS message forwarding."""

    def forward(self, msg: SmsMessage) -> None:
        """Forward an SMS message to an external service."""
        ...
