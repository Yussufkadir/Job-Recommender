import logging
import os

from app.ingestion.normalize import COUNTRY_NAMES, SUPPORTED_COUNTRIES
from app.sources.ats import ATS_SOURCES
from app.sources.base import JobSource
from app.sources.companies import COMPANY_BOARDS
from app.sources.job_apis import (
    AdzunaSource, ArbeitnowSource, JoobleSource, RemoteOKSource, RemotiveSource,
)

logger = logging.getLogger(__name__)

DEFAULT_SOURCE_KINDS = "ats,adzuna,arbeitnow,remotive,remoteok,jooble"
DEFAULT_QUERIES = (
    "software engineer,data scientist,data engineer,machine learning engineer,"
    "devops engineer,frontend developer,backend developer,product manager"
)


def _env_list(name: str, default: str) -> list[str]:
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


def _company_boards() -> list[tuple[str, str, str]]:
    boards = list(COMPANY_BOARDS)
    for entry in _env_list("JOB_EXTRA_BOARDS", ""):
        parts = entry.split(":", 2)
        if len(parts) < 2 or parts[0] not in ATS_SOURCES:
            logger.warning("Ignoring malformed JOB_EXTRA_BOARDS entry: %s", entry)
            continue
        boards.append((parts[0], parts[1], parts[2] if len(parts) == 3 else parts[1]))
    return boards


def build_sources() -> list[JobSource]:
    kinds = set(_env_list("JOB_SOURCES", DEFAULT_SOURCE_KINDS))
    countries = [c for c in _env_list("JOB_COUNTRIES", ",".join(SUPPORTED_COUNTRIES)) if c in SUPPORTED_COUNTRIES]
    sources: list[JobSource] = []

    if "ats" in kinds:
        sources += [ATS_SOURCES[ats](slug, company) for ats, slug, company in _company_boards()]

    if "adzuna" in kinds and AdzunaSource.is_configured():
        pages = int(os.getenv("ADZUNA_PAGES", "4"))
        sources += [AdzunaSource(country, pages=pages) for country in countries]

    if "arbeitnow" in kinds:
        sources.append(ArbeitnowSource(pages=int(os.getenv("ARBEITNOW_PAGES", "3"))))
    if "remotive" in kinds:
        sources.append(RemotiveSource())
    if "remoteok" in kinds:
        sources.append(RemoteOKSource())

    if "jooble" in kinds and JoobleSource.is_configured():
        for country in countries:
            for query in _env_list("JOB_INGEST_QUERIES", DEFAULT_QUERIES):
                sources.append(JoobleSource(query, COUNTRY_NAMES[country], country))

    return sources
