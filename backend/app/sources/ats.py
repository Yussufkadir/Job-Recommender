import logging
from typing import Iterable

from app.sources.base import JobSource, RawJob, get_json, html_to_text, parse_datetime

logger = logging.getLogger(__name__)


class GreenhouseSource(JobSource):
    def __init__(self, slug: str, company: str):
        self.slug = slug
        self.company = company
        self.name = f"greenhouse:{slug}"

    def fetch(self) -> Iterable[RawJob]:
        data = get_json(f"https://boards-api.greenhouse.io/v1/boards/{self.slug}/jobs", params={"content": "true"})
        for item in data.get("jobs", []):
            locations = [(item.get("location") or {}).get("name") or ""]
            locations += [office.get("location") or office.get("name") or "" for office in item.get("offices", [])]
            yield RawJob(
                source="greenhouse",
                external_id=f"{self.slug}:{item['id']}",
                title=item.get("title") or "",
                company=item.get("company_name") or self.company,
                description=html_to_text(item.get("content")),
                url=item.get("absolute_url") or "",
                location="; ".join(dict.fromkeys(loc for loc in locations if loc)),
                posted_at=parse_datetime(item.get("first_published") or item.get("updated_at")),
            )


class LeverSource(JobSource):
    def __init__(self, slug: str, company: str):
        self.slug = slug
        self.company = company
        self.name = f"lever:{slug}"

    def fetch(self) -> Iterable[RawJob]:
        data = get_json(f"https://api.lever.co/v0/postings/{self.slug}", params={"mode": "json"})
        for item in data if isinstance(data, list) else []:
            categories = item.get("categories") or {}
            locations = categories.get("allLocations") or [categories.get("location") or ""]
            parts = [item.get("openingPlain"), item.get("descriptionPlain")]
            for section in item.get("lists") or []:
                parts.append(section.get("text", ""))
                parts.append(html_to_text(section.get("content")))
            parts.append(item.get("additionalPlain"))
            country = (item.get("country") or "").lower()
            yield RawJob(
                source="lever",
                external_id=f"{self.slug}:{item['id']}",
                title=item.get("text") or "",
                company=self.company,
                description="\n".join(part.strip() for part in parts if part and part.strip()),
                url=item.get("hostedUrl") or "",
                location="; ".join(loc for loc in locations if loc),
                countries=[country] if country else [],
                remote=item.get("workplaceType") == "remote" or None,
                posted_at=parse_datetime(item.get("createdAt")),
            )


class AshbySource(JobSource):
    def __init__(self, slug: str, company: str):
        self.slug = slug
        self.company = company
        self.name = f"ashby:{slug}"

    def fetch(self) -> Iterable[RawJob]:
        data = get_json(f"https://api.ashbyhq.com/posting-api/job-board/{self.slug}")
        for item in data.get("jobs", []):
            if item.get("isListed") is False:
                continue
            locations = [item.get("location") or ""]
            locations += [loc.get("location") or "" for loc in item.get("secondaryLocations") or []]
            address = ((item.get("address") or {}).get("postalAddress") or {})
            if address.get("addressCountry"):
                locations.append(address["addressCountry"])
            yield RawJob(
                source="ashby",
                external_id=f"{self.slug}:{item['id']}",
                title=item.get("title") or "",
                company=self.company,
                description=(item.get("descriptionPlain") or html_to_text(item.get("descriptionHtml"))).strip(),
                url=item.get("jobUrl") or "",
                location="; ".join(dict.fromkeys(loc for loc in locations if loc)),
                remote=bool(item.get("isRemote")) or item.get("workplaceType") == "Remote" or None,
                posted_at=parse_datetime(item.get("publishedAt")),
            )


ATS_SOURCES = {
    "greenhouse": GreenhouseSource,
    "lever": LeverSource,
    "ashby": AshbySource,
}
