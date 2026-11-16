"""Which programming language a job or a search is about.

The skill signal treats every skill alike, so a Go backend job that shares Docker, AWS and
Postgres with a Python profile outranks a Python job. The main language decides who can
realistically do a job, so the ranker lowers jobs whose languages don't overlap the
search's (see rank_jobs). Frameworks count as their language: "django" means Python.

A lookup table rather than a model: whether "kotlin" is a language never depends on
context, and the NER already decides what is a skill in the first place.
"""
import re
from typing import Iterable

# skill or framework (lowercased, as the NER extracts it) -> language family
LANGUAGE_OF = {
    "python": "python", "django": "python", "flask": "python", "fastapi": "python",
    "java": "java", "spring": "java", "spring boot": "java", "hibernate": "java",
    "kotlin": "kotlin", "ktor": "kotlin",
    "go": "go", "golang": "go",
    "ruby": "ruby", "rails": "ruby", "ruby on rails": "ruby",
    "c#": "csharp", ".net": "csharp", "dotnet": "csharp", "asp.net": "csharp", ".net core": "csharp",
    "php": "php", "laravel": "php", "symfony": "php",
    "rust": "rust",
    "scala": "scala",
    "elixir": "elixir", "phoenix": "elixir",
    "c++": "cpp",
    "swift": "swift", "swiftui": "swift", "objective-c": "swift",
    "dart": "dart", "flutter": "dart",
    "abap": "abap",
    # JavaScript and TypeScript are one family: the same developers, the same jobs.
    "javascript": "js", "typescript": "js", "node": "js", "node.js": "js", "nodejs": "js",
    "react": "js", "react.js": "js", "angular": "js", "vue": "js", "vue.js": "js",
    "next.js": "js", "nestjs": "js", "express": "js", "svelte": "js",
}

# Languages named in a job title, e.g. "Backend Engineer (Golang)", "Java Entwickler".
# "go" only as a standalone word that isn't "go-to-market" or "on the go".
_TITLE_PATTERNS = [
    (re.compile(r"\bpython\b|\bdjango\b"), "python"),
    (re.compile(r"\bjava\b(?!\s*script)|\bspring\b"), "java"),
    (re.compile(r"\bkotlin\b"), "kotlin"),
    (re.compile(r"\bgolang\b|(?<![\w-])go(?![\w-])(?!\s+to\b)"), "go"),
    (re.compile(r"\bruby\b|\brails\b"), "ruby"),
    (re.compile(r"(?<![\w])c#|\.net\b|\bdotnet\b"), "csharp"),
    (re.compile(r"\bphp\b|\blaravel\b|\bsymfony\b"), "php"),
    (re.compile(r"\brust\b"), "rust"),
    (re.compile(r"\bscala\b"), "scala"),
    (re.compile(r"\belixir\b"), "elixir"),
    (re.compile(r"(?<![\w])c\+\+"), "cpp"),
    (re.compile(r"\bswift\b|\bios\b"), "swift"),
    (re.compile(r"\bflutter\b|\bdart\b"), "dart"),
    (re.compile(r"\babap\b"), "abap"),
    (re.compile(r"\bjavascript\b|\btypescript\b|\bnode(?:\.?js)?\b|\breact\b|\bangular\b|\bvue\b"), "js"),
]


# Languages mentioned in a description. Case-sensitive, so "Go" (the language) isn't "go"
# (the verb); a capitalized "Go" counts only next to programming context ("in Go", "Go,",
# "Go services") so "Go further" at the start of a sentence doesn't.
_TEXT_PATTERNS = [
    (re.compile(r"\bPython\b|\bDjango\b|\bFastAPI\b|\bFlask\b"), "python"),
    (re.compile(r"\bJava\b(?!\s*[Ss]cript)|\bSpring Boot\b"), "java"),
    (re.compile(r"\bKotlin\b"), "kotlin"),
    (re.compile(r"\bGolang\b|\bGo\b(?!-)(?=\s*(?:[,/)]|and\b|or\b|developer|engineer|service|microservice|code"
                r"|programming|experience|backend|\d))|(?:(?<=\bin )|(?<=\busing )|(?<=\bwith )|(?<=\())Go\b(?!-)"), "go"),
    (re.compile(r"\bRuby\b|\bRails\b"), "ruby"),
    (re.compile(r"(?<![\w])C#|\.NET\b"), "csharp"),
    (re.compile(r"\bPHP\b|\bLaravel\b|\bSymfony\b"), "php"),
    (re.compile(r"\bRust\b"), "rust"),
    (re.compile(r"\bScala\b"), "scala"),
    (re.compile(r"\bElixir\b"), "elixir"),
    (re.compile(r"(?<![\w])C\+\+"), "cpp"),
    (re.compile(r"\bSwift(?:UI)?\b"), "swift"),
    (re.compile(r"\bFlutter\b|\bDart\b"), "dart"),
    (re.compile(r"\bABAP\b"), "abap"),
    (re.compile(r"\bJavaScript\b|\bTypeScript\b|\bNode(?:\.?js)?\b|\bReact\b|\bAngular\b|\bVue(?:\.js)?\b"), "js"),
]


def languages_of_skills(skills: Iterable[str]) -> frozenset[str]:
    return frozenset(language for skill in skills if (language := LANGUAGE_OF.get(skill.strip().lower())))


def languages_of_title(title: str) -> frozenset[str]:
    lowered = title.lower()
    return frozenset(language for pattern, language in _TITLE_PATTERNS if pattern.search(lowered))


def languages_of_text(text: str) -> frozenset[str]:
    return frozenset(language for pattern, language in _TEXT_PATTERNS if pattern.search(text))


def job_languages(title: str, skills: Iterable[str], description: str = "") -> frozenset[str]:
    """A language in the title is the job's main language. Otherwise every language the
    extracted skills or the description mention: the NER finds no skills at all in most job
    postings, so the text is read directly."""
    return languages_of_title(title) or (languages_of_skills(skills) | languages_of_text(description))


def search_languages(query: str, skills: Iterable[str]) -> frozenset[str]:
    return languages_of_title(query) | languages_of_skills(skills)
