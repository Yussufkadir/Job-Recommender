import re

_PHRASES = [
    (re.compile(r"\bfront[\s-]+end\b"), "frontend"),
    (re.compile(r"\bback[\s-]+end\b"), "backend"),
    (re.compile(r"\bfull[\s-]+stack\b"), "fullstack"),
    (re.compile(r"\bmachine learning\b"), "ml"),
    (re.compile(r"\bartificial intelligence\b"), "ai"),
    (re.compile(r"\bsite reliability\b"), "sre"),
    (re.compile(r"\bdev[\s-]?ops\b"), "devops"),
    (re.compile(r"\b(react|node|vue|next|nest|express)\.?js\b"), r"\1"),
]
_SYNONYMS = {
    "developer": "engineer", "developers": "engineer", "dev": "engineer", "programmer": "engineer",
    "engineers": "engineer", "engineering": "engineer", "swe": "engineer", "entwickler": "engineer",
    "softwareentwickler": "engineer", "scientists": "scientist", "analysts": "analyst",
    "golang": "go", "k8s": "kubernetes", "postgresql": "postgres", "javascript": "js", "typescript": "ts",
    "managers": "manager", "designers": "designer",
}
_STOPWORDS = {
    "a", "an", "and", "the", "of", "for", "in", "on", "at", "to", "with", "or", "by", "as", "is",
    "m", "w", "f", "d", "x", "mwd", "fmd", "all", "genders", "job", "role", "position", "remote",
    "hybrid", "onsite", "team", "new",
}
_TOKEN = re.compile(r"[a-z0-9][a-z0-9+#]*")


def tokenize(text: str) -> list[str]:
    lowered = text.lower()
    for pattern, replacement in _PHRASES:
        lowered = pattern.sub(replacement, lowered)
    tokens = []
    for token in _TOKEN.findall(lowered):
        token = _SYNONYMS.get(token, token)
        if token not in _STOPWORDS:
            tokens.append(token)
    return tokens
