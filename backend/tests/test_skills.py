import pytest

from app.ingestion.normalize import clean_skills
from app.matching.skills import job_skills, skills_in_text


@pytest.mark.parametrize("text, expected", [
    ("We use Python, Django and Postgres on AWS.", {"python", "django", "postgresql", "aws"}),
    ("Deploys run on K8s via GitHub Actions.", {"kubernetes", "github actions"}),
    ("Frontend in React and TypeScript, backend in Go.", {"react", "typescript", "go"}),
    ("Node.js services, C# tools and C++ engines.", {"node.js", "c#", "c++"}),
    ("Experience with Spark and Excel.", {"spark", "excel"}),
])
def test_skills_in_text_finds_common_tools(text, expected):
    assert expected <= skills_in_text(text)


@pytest.mark.parametrize("text", [
    "You react quickly and excel at communication.",
    "Take the helm of a team that loves to go further.",
    "Our javascript-free pages",  # "java" inside another word
    "Spring 2026 internship. Express interest below.",
])
def test_skills_in_text_ignores_ordinary_words(text):
    assert not skills_in_text(text) - {"javascript"}


def test_job_skills_drops_the_hiring_companys_name():
    skills = job_skills(["databricks", "python"], "Data Engineer", "Build on Databricks and Spark.", "Databricks Inc")
    assert "databricks" not in skills
    assert {"python", "spark"} <= set(skills)


def test_clean_skills_drops_hiring_policy_terms_benefits_and_companies():
    assert clean_skills(["Python", "sexual orientation", "veteran status", "health insurance", "Lyft",
                         "amazon rsus"]) == ["python"]
