"""Job aggregator APIs that offer official access."""
import logging
import os
from typing import Iterable, Optional

import requests

from app.sources.base import (
    REQUEST_TIMEOUT, USER_AGENT, JobSource, RawJob, fix_mojibake, get_json, html_to_text, parse_datetime,
)

logger = logging.getLogger(__name__)


class AdzunaSource(JobSource):
    RESULTS_PER_PAGE = 50

    def __init__(
        self,
        country: str,
        pages: int = 4,
        category: Optional[str] = "it-jobs",
        what: Optional[str] = None,
        what_or: Optional[str] = None,
        where: Optional[str] = None,
        max_days_old: int = 30,
    ):
        self.country = country
        self.pages = pages
        self.category = category
        self.what = what
        self.what_or = what_or
        self.where = where
        self.max_days_old = max_days_old
        self.app_id = os.getenv("ADZUNA_APPLICATION_ID")
        self.app_key = os.getenv("ADZUNA_APPLICATION_KEY")
        self.name = f"adzuna:{country}" + (f":{what}" if what else "")

    @staticmethod
    def is_configured() -> bool:
        return bool(os.getenv("ADZUNA_APPLICATION_ID") and os.getenv("ADZUNA_APPLICATION_KEY"))

    def _params(self, page: int) -> dict:
        params = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "results_per_page": self.RESULTS_PER_PAGE,
            "max_days_old": self.max_days_old,
            "sort_by": "date",
            "content-type": "application/json",
        }
        optional = {
            "category": self.category,
            "what": self.what,
            "what_or": self.what_or,
            "where": self.where,
        }
        params.update({key: value for key, value in optional.items() if value})
        return params

    def fetch(self) -> Iterable[RawJob]:
        if not self.is_configured():
            logger.info("Adzuna keys not set; skipping %s", self.name)
            return
        for page in range(1, self.pages + 1):
            data = get_json(
                f"https://api.adzuna.com/v1/api/jobs/{self.country}/search/{page}",
                params=self._params(page),
            )
            results = data.get("results", [])
            for item in results:
                yield RawJob(
                    source="adzuna",
                    external_id=f"{self.country}:{item['id']}",
                    title=html_to_text(item.get("title")),
                    company=(item.get("company") or {}).get("display_name") or "Unknown company",
                    description=html_to_text(item.get("description")),
                    url=item.get("redirect_url") or "",
                    location=(item.get("location") or {}).get("display_name"),
                    countries=[self.country],
                    posted_at=parse_datetime(item.get("created")),
                )
            if len(results) < self.RESULTS_PER_PAGE:
                break


class ArbeitnowSource(JobSource):
    name = "arbeitnow"

    def __init__(self, pages: int = 3):
        self.pages = pages

    def fetch(self) -> Iterable[RawJob]:
        for page in range(1, self.pages + 1):
            data = get_json("https://www.arbeitnow.com/api/job-board-api", params={"page": page})
            for item in data.get("data", []):
                yield RawJob(
                    source="arbeitnow",
                    external_id=item["slug"],
                    title=item.get("title") or "",
                    company=item.get("company_name") or "Unknown company",
                    description=html_to_text(item.get("description")),
                    url=item.get("url") or "",
                    location=item.get("location"),
                    remote=bool(item.get("remote")) or None,
                    posted_at=parse_datetime(item.get("created_at")),
                    default_country="de",
                )
            if not (data.get("links") or {}).get("next"):
                break


class RemotiveSource(JobSource):
    name = "remotive"

    def fetch(self) -> Iterable[RawJob]:
        data = get_json("https://remotive.com/api/remote-jobs")
        for item in data.get("jobs", []):
            yield RawJob(
                source="remotive",
                external_id=str(item["id"]),
                title=item.get("title") or "",
                company=item.get("company_name") or "Unknown company",
                description=html_to_text(item.get("description")),
                url=item.get("url") or "",
                location=item.get("candidate_required_location") or "Worldwide",
                remote=True,
                posted_at=parse_datetime(item.get("publication_date")),
            )


class RemoteOKSource(JobSource):
    name = "remoteok"

    def fetch(self) -> Iterable[RawJob]:
        data = get_json("https://remoteok.com/api")
        for item in data:
            if not isinstance(item, dict) or "id" not in item or "position" not in item:
                continue  # the first element is the legal notice
            yield RawJob(
                source="remoteok",
                external_id=str(item["id"]),
                # RemoteOK's API returns double-encoded text.
                title=fix_mojibake(item.get("position")),
                company=fix_mojibake(item.get("company")) or "Unknown company",
                description=html_to_text(fix_mojibake(item.get("description"))),
                url=item.get("url") or "",
                location=fix_mojibake(item.get("location")) or "Worldwide",
                remote=True,
                posted_at=parse_datetime(item.get("epoch") or item.get("date")),
            )


class JoobleSource(JobSource):

    def __init__(self, keywords: str, location: str, country: str):
        self.keywords = keywords
        self.location = location
        self.country = country
        self.api_key = os.getenv("JOOBLE_API_KEY")
        self.name = f"jooble:{country}:{keywords}"

    @staticmethod
    def is_configured() -> bool:
        return bool(os.getenv("JOOBLE_API_KEY"))

    def fetch(self) -> Iterable[RawJob]:
        if not self.api_key:
            return
        response = requests.post(
            f"https://jooble.org/api/{self.api_key}",
            json={"keywords": self.keywords, "location": self.location},
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        for item in response.json().get("jobs", []):
            yield RawJob(
                source="jooble",
                external_id=str(item.get("id") or item.get("link")),
                title=html_to_text(item.get("title")),
                company=item.get("company") or "Unknown company",
                description=html_to_text(item.get("snippet")),
                url=item.get("link") or "",
                location=item.get("location"),
                countries=[self.country],
                posted_at=parse_datetime(item.get("updated")),
            )
