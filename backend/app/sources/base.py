import html
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterable, Optional

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

USER_AGENT = "JobRecommender/0.2 (+https://github.com/Yussufkadir/Job-Recommender)"
REQUEST_TIMEOUT = 30


@dataclass
class RawJob:
    source: str
    external_id: str
    title: str
    company: str
    description: str
    url: str
    location: Optional[str] = None
    countries: list[str] = field(default_factory=list)
    remote: Optional[bool] = None
    posted_at: Optional[datetime] = None
    default_country: Optional[str] = None


class JobSource:
    name: str = "source"

    def fetch(self) -> Iterable[RawJob]:
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"<{type(self).__name__} {self.name}>"


_session = requests.Session()
_session.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})


def get_json(url: str, **kwargs):
    kwargs.setdefault("timeout", REQUEST_TIMEOUT)
    response = _session.get(url, **kwargs)
    response.raise_for_status()
    return response.json()


def html_to_text(value: Optional[str]) -> str:
    if not value:
        return ""
    unescaped = html.unescape(value)
    if "<" not in unescaped:
        return unescaped.strip()
    soup = BeautifulSoup(unescaped, "html.parser")
    for tag in soup.find_all(["br", "p", "li", "h1", "h2", "h3", "h4", "div"]):
        tag.insert_before("\n")
    text = soup.get_text()
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line).strip()


def fix_mojibake(value: Optional[str]) -> str:
    if not value or not any(marker in value for marker in ("â\x80", "Ã", "Â")):
        return value or ""
    try:
        return value.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return value


def parse_datetime(value) -> Optional[datetime]:
    if value in (None, ""):
        return None
    try:
        if isinstance(value, (int, float)):
            seconds = value / 1000 if value > 10_000_000_000 else value
            return datetime.fromtimestamp(seconds, tz=timezone.utc)
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except (ValueError, OverflowError, OSError):
        return None
