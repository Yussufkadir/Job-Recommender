"""Skills of a job: the NER's, cleaned, plus well-known tools named in the posting.

The NER was trained on CVs and finds no skills at all in most job postings (64% of the
evaluation snapshot), and misses common tools in many of the rest (Docker in 17 of 10,000
jobs). Those jobs then get no skill signal, however well they fit. A word list of common tools
fills the gap: whether "kubernetes" is a skill never depends on context.
"""
import re

from app.ingestion.normalize import clean_skills, same_company

# variant as written in a posting (lowercased) -> the skill name the scoring model knows
_SKILLS = {
    # languages
    "python": "python", "java": "java", "kotlin": "kotlin", "golang": "go", "scala": "scala",
    "typescript": "typescript", "javascript": "javascript", "c#": "c#", "c++": "c++", "php": "php",
    "elixir": "elixir", "haskell": "haskell", "erlang": "erlang", "clojure": "clojure", "matlab": "matlab",
    "sql": "sql", "nosql": "nosql", "html": "html", "css": "css", "sass": "sass", "bash": "bash",
    "powershell": "powershell", "abap": "abap", "objective-c": "objective-c",
    # backend frameworks
    "django": "django", "flask": "flask", "fastapi": "fastapi", "spring boot": "spring boot",
    "hibernate": "hibernate", "node.js": "node.js", "nodejs": "node.js", "nestjs": "nestjs",
    "ruby on rails": "ruby on rails", ".net": ".net", "asp.net": "asp.net", "laravel": "laravel",
    "symfony": "symfony", "graphql": "graphql", "grpc": "grpc", "rest api": "rest api",
    "rest apis": "rest api", "restful": "rest api", "microservices": "microservices", "kafka": "kafka",
    "rabbitmq": "rabbitmq",
    # frontend and mobile
    "next.js": "next.js", "vue": "vue", "vue.js": "vue", "redux": "redux", "tailwind": "tailwind",
    "webpack": "webpack", "vite": "vite", "jest": "jest", "cypress": "cypress", "playwright": "playwright",
    "selenium": "selenium", "storybook": "storybook", "react native": "react native", "flutter": "flutter",
    "swiftui": "swiftui", "jetpack compose": "jetpack compose", "android": "android", "ios": "ios",
    "figma": "figma",
    # databases and data
    "postgresql": "postgresql", "postgres": "postgresql", "mysql": "mysql", "mongodb": "mongodb",
    "redis": "redis", "elasticsearch": "elasticsearch", "cassandra": "cassandra", "dynamodb": "dynamodb",
    "bigquery": "bigquery", "redshift": "redshift", "databricks": "databricks", "dbt": "dbt",
    "airflow": "airflow", "pyspark": "pyspark", "hadoop": "hadoop", "flink": "flink", "etl": "etl",
    "data warehousing": "data warehousing", "data modeling": "data modeling", "tableau": "tableau",
    "power bi": "power bi", "looker": "looker", "pandas": "pandas", "numpy": "numpy",
    # machine learning
    "machine learning": "machine learning", "deep learning": "deep learning", "pytorch": "pytorch",
    "tensorflow": "tensorflow", "keras": "keras", "scikit-learn": "scikit-learn", "sklearn": "scikit-learn",
    "hugging face": "hugging face", "nlp": "nlp", "computer vision": "computer vision", "llm": "llm",
    "llms": "llm", "langchain": "langchain", "mlops": "mlops", "mlflow": "mlflow", "kubeflow": "kubeflow",
    "sagemaker": "sagemaker", "statistics": "statistics", "a/b testing": "a/b testing", "xgboost": "xgboost",
    # cloud and operations
    "aws": "aws", "gcp": "gcp", "google cloud": "gcp", "azure": "azure", "docker": "docker",
    "kubernetes": "kubernetes", "k8s": "kubernetes", "terraform": "terraform", "ansible": "ansible",
    "pulumi": "pulumi", "cloudformation": "cloudformation", "ci/cd": "ci/cd", "jenkins": "jenkins",
    "github actions": "github actions", "gitlab ci": "gitlab ci", "argo cd": "argo cd", "argocd": "argo cd",
    "prometheus": "prometheus", "grafana": "grafana", "datadog": "datadog", "istio": "istio",
    "openshift": "openshift", "nginx": "nginx", "linux": "linux", "git": "git", "jira": "jira",
    "agile": "agile", "scrum": "scrum",
}
_SKILL_PATTERN = re.compile(
    r"(?<![\w.+#/-])(?:" + "|".join(sorted(map(re.escape, _SKILLS), key=len, reverse=True)) + r")(?![\w+#-])"
)

# Names that are also ordinary English words ("react to", "excel at", "at the helm") only count
# capitalized. "Spring" and "Express" are left out: "Spring 2026", "Express interest".
_CAPITALIZED_SKILLS = {
    "React": "react", "Angular": "angular", "Spark": "spark", "Excel": "excel", "Helm": "helm",
    "Rust": "rust", "Swift": "swift", "Ruby": "ruby", "Rails": "ruby on rails", "Dart": "dart",
    "Snowflake": "snowflake", "Go": "go",
}
_CAPITALIZED_PATTERN = re.compile(r"(?<![\w.-])(?:" + "|".join(_CAPITALIZED_SKILLS) + r")(?![\w-])")
# "Go" counts only when it reads as the language: "in Go", "Go,", "Go services".
_GO_PATTERN = re.compile(
    r"\bGo\b(?!-)(?=\s*(?:[,/)]|and\b|or\b|developer|engineer|service|microservice|code|programming|experience|backend))"
    r"|(?:(?<=\bin )|(?<=\busing )|(?<=\bwith )|(?<=\())Go\b(?!-)"
)


def skills_in_text(text: str) -> set[str]:
    found = {_SKILLS[match.group(0)] for match in _SKILL_PATTERN.finditer(text.lower())}
    for match in _CAPITALIZED_PATTERN.finditer(text):
        if match.group(0) != "Go":
            found.add(_CAPITALIZED_SKILLS[match.group(0)])
    if _GO_PATTERN.search(text):
        found.add("go")
    return found


def job_skills(extracted: list[str], title: str, description: str, company: str) -> list[str]:
    """The NER's skills plus the word-list skills found in the title and description, without
    the hiring company's own name ("lyft" at Lyft, "databricks" at Databricks)."""
    found = set(clean_skills(extracted)) | skills_in_text(f"{title}\n{description}")
    return sorted(skill for skill in found if not same_company(skill, company))
