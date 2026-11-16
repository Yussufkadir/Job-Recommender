import numpy as np
import pytest

from app.matching.languages import job_languages, languages_of_text, search_languages


@pytest.mark.parametrize("title, skills, description, expected", [
    ("Senior Backend Engineer (Golang)", ["python"], "", {"go"}),  # the title names the main language
    ("Java Entwickler:in", [], "", {"java"}),
    ("JavaScript Developer", [], "", {"js"}),
    ("Senior Backend Engineer", [], "Production experience with Kotlin, Java or Golang.", {"kotlin", "java", "go"}),
    ("Senior Backend Engineer", ["django"], "", {"python"}),  # frameworks count as their language
    ("Data Analyst", ["sql", "excel"], "Go further with us.", set()),
    ("Go-to-market Manager", [], "", set()),
])
def test_job_languages(title, skills, description, expected):
    assert job_languages(title, skills, description) == expected


@pytest.mark.parametrize("text, expected", [
    ("written in Go and Python", {"go", "python"}),
    ("services in Go", {"go"}),
    ("Let's go! Go further.", set()),
    ("our go-to-market team", set()),
    ("React, TypeScript and Node.js", {"js"}),
])
def test_languages_of_text(text, expected):
    assert languages_of_text(text) == expected


def test_search_languages():
    assert search_languages("Backend Engineer", ["Python", "Django", "PostgreSQL"]) == {"python"}
    assert search_languages("DevOps Engineer", ["Kubernetes", "Terraform", "AWS"]) == set()
    assert search_languages("Java Developer", ["Spring Boot", "SQL"]) == {"java"}
