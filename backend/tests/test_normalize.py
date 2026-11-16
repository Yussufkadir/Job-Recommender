import pytest

from app.ingestion.normalize import (
    EUROPE, SUPPORTED_COUNTRIES, clean_skills, clean_title, dedupe_key, infer_countries, is_remote,
    looks_english, names_unsupported_place, same_company, seniority_from_title,
)
from app.sources.base import fix_mojibake


@pytest.mark.parametrize("location, expected", [
    ("Berlin, Germany", ["de"]),
    ("Warszawa, mazowieckie", ["pl"]),
    ("Remote - US", ["us"]),
    ("New York, NY; London, UK", ["gb", "us"]),
    ("Toronto, ON", ["ca"]),
    ("Berlin, DE", ["de"]),  
    ("Amsterdam, NL", ["nl"]),  
    ("Columbus, Ohio", ["us"]),
    ("Remote, Europe", EUROPE),
    ("Worldwide", SUPPORTED_COUNTRIES),
    ("Singapore", []),
    ("Remote", []),
    ("Frankfurt | Global Team", ["de"]),
    ("Sydney, New South Wales, Australia", []),
    ("Boston, New England", ["us"]),
    (None, []),
])
def test_infer_countries(location, expected):
    assert infer_countries(location) == expected


def test_is_remote():
    assert is_remote("Remote - EU")
    assert is_remote("Berlin", flag=True)
    assert not is_remote("Berlin, Germany")


@pytest.mark.parametrize("title, level", [
    ("Senior Backend Engineer", "senior"),
    ("Staff Engineer", "senior"),
    ("Werkstudent Data (m/w/d)", "intern"),
    ("Junior Frontend Developer", "junior"),
    ("Software Engineer II", "mid"),
])
def test_seniority_from_title(title, level):
    assert seniority_from_title(title) == level


def test_dedupe_key_ignores_gender_tags_and_company_suffixes():
    assert dedupe_key("Data Engineer (m/w/d)", "Acme GmbH") == dedupe_key("Data Engineer", "Acme")


def test_same_company_handles_board_display_names():
    assert same_company("wolt", "Wolt - English")
    assert same_company("Stripe, Inc.", "stripe")
    assert not same_company("Meta", "Metaview")


def test_clean_title_and_skills():
    assert clean_title("Python &amp; Cloud Engineer (m/w/d)") == "Python & Cloud Engineer"
    assert clean_skills(["Python", "amp", "front-end changes submitted through pull requests", "a\nb", "SQL"]) == [
        "python", "sql",
    ]


def test_unsupported_places_block_default_country():
    assert names_unsupported_place("Schlieren")
    assert names_unsupported_place("Wien, Austria")
    assert not names_unsupported_place("Berlin")


def test_fix_mojibake():
    assert fix_mojibake("â\x80¢ Lead the team") == "• Lead the team"
    assert fix_mojibake("Zürich") == "Zürich"


def test_looks_english():
    english = ("We are looking for an experienced engineer to join our team in Berlin. You will work "
               "with Python and be responsible for building new features and maintaining our systems.")
    german = ("Wir suchen einen erfahrenen Entwickler für unser Team in Berlin. Du arbeitest mit Python "
              "und bist verantwortlich für die Entwicklung neuer Funktionen und die Wartung der Systeme.")
    assert looks_english(english)
    assert not looks_english(german)
