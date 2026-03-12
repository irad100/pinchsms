import re

from pydantic import BaseModel


class SmsMessage(BaseModel, frozen=True):
    index: int
    sender: str
    timestamp: str
    body: str


_CMGL_HEADER = re.compile(
    r"\+CMGL:\s*(\d+)\s*,"  # index
    r'\s*"[^"]*"\s*,'  # status (ignored)
    r'\s*"([^"]*)"\s*,'  # sender
    r"\s*[^,]*,"  # alpha field (ignored)
    r'\s*"?([^"]*)"?'  # timestamp (rest of header)
)


def parse_message_listing(raw: str) -> list[SmsMessage]:
    """Parse AT+CMGL response into a list of SmsMessage objects."""
    messages: list[SmsMessage] = []
    lines = raw.strip().split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        match = _CMGL_HEADER.match(line)
        if match:
            index = int(match.group(1))
            sender = match.group(2)
            timestamp = match.group(3).strip().strip('"')
            body_lines: list[str] = []
            i += 1
            while i < len(lines):
                cur = lines[i].strip()
                if cur.startswith("+CMGL:") or cur == "OK":
                    break
                if cur:
                    body_lines.append(cur)
                i += 1
            messages.append(
                SmsMessage(
                    index=index,
                    sender=sender,
                    timestamp=timestamp,
                    body="\n".join(body_lines),
                )
            )
        else:
            i += 1
    return messages
