"""Label Studio annotations for the resume NER model: loading, parsing, filling skipped skills.

Shared by NER_preparation.ipynb (building the training data), evaluate_ner.py (scoring
the model) and review_auto_labels.py (checking the automatic labels by hand), so all three
see exactly the same labels.

Why filling: to save time, CVs were labeled partially. A skill was often labeled once and
its other mentions skipped, and some skills were skipped in a CV altogether (Docker is
labeled in half of the CVs that mention it). Unlabeled mentions teach the model that the
word is *not* a skill, and in evaluation they turn correct predictions into false positives.

fill_skill_spans() labels every whole-word mention of a known skill:
- skills labeled in this CV, plus skills labeled often enough overall (MIN_LABELED_CVS,
  MIN_LABEL_RATE) to be trusted as skills wherever they appear;
- except everyday English words ("rest", "spring", "react" as single words), which stay
  labeled only where a person labeled them; phrases like "spring boot" are still filled;
- except phrases labeled more often as another entity ("system administrator" is a TITLE);
- longest match first, so "sql server" wins over "sql" and "java script" isn't "java".
"""
import itertools
import json
import random
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Iterable, Optional

SPLIT_SEED = 23
DEV_RATIO = 0.2
MAX_SKILL_TOKENS = 4
# To be filled into other CVs, a skill must be labeled in at least MIN_LABELED_CVS CVs and in
# at least MIN_LABEL_RATE of the CVs that mention it. Real skills that were often skipped still
# clear the rate (azure 24%, angular 22%); generic words labeled now and then don't
# ("servers" 4%, "configuration" 3%).
MIN_LABELED_CVS = 3
MIN_LABEL_RATE = 0.15
# Single words at least this common in everyday English (wordfreq Zipf scale: "rest" 5.2,
# "react" 4.2, "java" 4.0, "python" 3.8, "docker" 3.0) are not filled automatically.
EVERYDAY_WORD_ZIPF = 4.1

Span = tuple[int, int, str]
_TOKEN = re.compile(r"[a-z0-9+#]+")


def load_items(json_path: str) -> list:
    """Label Studio export as a flat list of tasks (nested single-item lists are unwrapped)."""
    with open(json_path, "r", encoding="utf-8", errors="replace") as handle:
        data = json.load(handle)
    while isinstance(data, list) and len(data) == 1 and isinstance(data[0], list):
        data = data[0]
    if isinstance(data, list) and data and all(isinstance(x, list) for x in data):
        data = list(itertools.chain.from_iterable(data))
    if not isinstance(data, list):
        raise ValueError("Unexpected JSON root type: expected list")
    return data


def item_text(item) -> str:
    if not isinstance(item, dict):
        return ""
    candidates = [item.get("text"), item.get("content"), item.get("resume")]
    data_block = item.get("data") if isinstance(item.get("data"), dict) else {}
    candidates += [data_block.get("text"), data_block.get("content"), data_block.get("resume")]
    return next((c for c in candidates if isinstance(c, str) and c.strip()), "")


def item_id(item) -> str:
    return str(item.get("id", "")) if isinstance(item, dict) else ""


def normalize_label(label) -> Optional[str]:
    """'skill', 'B-SKILL' -> 'SKILL'; PER/MISC are not trained, so they map to None."""
    label = str(label or "").strip().upper()
    if label.startswith(("B-", "I-")):
        label = label.split("-", 1)[1]
    return None if label in ("", "PER", "MISC") else label


def item_spans(item) -> list[Span]:
    """Spans from either Label Studio (annotations[].result[].value) or plain [start, end, label]."""
    if not isinstance(item, dict):
        return []
    raw = item.get("annotations") or item.get("spans") or item.get("entities") or []
    spans: list[Span] = []

    def add(start, end, label):
        try:
            start, end = int(start), int(end)
        except (TypeError, ValueError):
            return
        label = normalize_label(label)
        if label and start < end:
            spans.append((start, end, label))

    def parse_result(result):
        value = result.get("value") if isinstance(result.get("value"), dict) else {}
        start = value.get("start", result.get("start"))
        end = value.get("end", result.get("end"))
        labels = value.get("labels") or result.get("labels")
        label = labels[0] if isinstance(labels, list) and labels else (value.get("label") or result.get("label"))
        add(start, end, label)

    for annotation in raw if isinstance(raw, list) else [raw]:
        if isinstance(annotation, dict) and "result" in annotation:
            for result in annotation.get("result") or []:
                if isinstance(result, dict):
                    parse_result(result)
        elif isinstance(annotation, dict):
            parse_result(annotation)
        elif isinstance(annotation, (list, tuple)) and len(annotation) >= 3:
            add(*annotation[:3])
    return spans


def normalize_skill(text: str) -> str:
    """'Node.js', 'node js' and 'NodeJS'-style spacing variants share one form: 'node js'."""
    return " ".join(_TOKEN.findall(text.lower()))


def _ngrams(text: str) -> set[str]:
    tokens = _TOKEN.findall(text.lower())
    return {" ".join(tokens[i:i + n]) for n in range(1, MAX_SKILL_TOKENS + 1) for i in range(len(tokens) - n + 1)}


def _pattern(skill: str) -> re.Pattern:
    """Whole-word pattern; separators between tokens may be space, '.', '-', '/' or nothing."""
    tokens = [re.escape(token) for token in skill.split()]
    return re.compile(r"(?<![\w+#.])" + r"[\s.\-/]*".join(tokens) + r"(?![\w+#])", re.IGNORECASE)


def _is_everyday_word(skill: str) -> bool:
    try:
        from wordfreq import zipf_frequency
    except ImportError as error:  # pragma: no cover
        raise ImportError("Label filling needs wordfreq: pip install wordfreq==3.1.1") from error
    return " " not in skill and zipf_frequency(skill, "en") >= EVERYDAY_WORD_ZIPF


@dataclass
class SkillVocabulary:
    """Which skills may be filled into CVs, learned from the labels themselves."""
    known: set[str] = field(default_factory=set)       # trusted as a skill wherever it appears
    blocked: set[str] = field(default_factory=set)     # everyday words or mostly another entity
    labeled_cvs: Counter = field(default_factory=Counter)
    mentioned_cvs: Counter = field(default_factory=Counter)

    def label_rate(self, skill: str) -> float:
        return self.labeled_cvs[skill] / max(self.mentioned_cvs[skill], self.labeled_cvs[skill], 1)

    def allows(self, skill: str) -> bool:
        return bool(skill) and skill not in self.blocked


def build_vocabulary(items: Iterable) -> SkillVocabulary:
    vocabulary = SkillVocabulary()
    other_label_cvs = Counter()
    texts = []
    for item in items:
        text = item_text(item)
        spans = item_spans(item)
        texts.append(text)
        vocabulary.labeled_cvs.update({normalize_skill(text[s:e]) for s, e, label in spans if label == "SKILL"} - {""})
        other_label_cvs.update({normalize_skill(text[s:e]) for s, e, label in spans if label != "SKILL"} - {""})
    candidates = set()
    for skill, count in vocabulary.labeled_cvs.items():
        if _is_everyday_word(skill) or other_label_cvs[skill] >= count:
            vocabulary.blocked.add(skill)
        elif count >= MIN_LABELED_CVS:
            candidates.add(skill)
    for text in texts:
        vocabulary.mentioned_cvs.update(_ngrams(text) & candidates)
    vocabulary.known = {skill for skill in candidates if vocabulary.label_rate(skill) >= MIN_LABEL_RATE}
    return vocabulary


def fill_skill_spans(text: str, spans: list[Span], vocabulary: SkillVocabulary) -> list[Span]:
    """New SKILL spans for unlabeled mentions of skills labeled in this CV or known overall."""
    own = {normalize_skill(text[s:e]) for s, e, label in spans if label == "SKILL"}
    candidates = {skill for skill in (own | (_ngrams(text) & vocabulary.known)) if vocabulary.allows(skill)}

    matches = []
    for skill in candidates:
        matches += [match.span() for match in _pattern(skill).finditer(text)]
    taken = [(start, end) for start, end, _ in spans]
    added: list[Span] = []
    for start, end in sorted(set(matches), key=lambda span: (span[0] - span[1], span[0])):  # longest first
        if not any(start < t_end and end > t_start for t_start, t_end in taken):
            added.append((start, end, "SKILL"))
            taken.append((start, end))
    return sorted(added)


def propagate_labels(data: list, vocabulary: Optional[SkillVocabulary] = None, verbose: bool = True) -> list:
    """Fill skipped skills into every task, appended to its annotations as [start, end, "SKILL"]
    entries, which the notebook's annotation parser reads alongside Label Studio results."""
    vocabulary = build_vocabulary(data) if vocabulary is None else vocabulary
    added_total = 0
    for item in data:
        text = item_text(item)
        if not text:
            continue
        added = fill_skill_spans(text, item_spans(item), vocabulary)
        if added:
            annotations = item.get("annotations")
            if not isinstance(annotations, list):
                annotations = [annotations] if annotations else []
                item["annotations"] = annotations
            annotations.extend([start, end, label] for start, end, label in added)
            added_total += len(added)
    if verbose:
        print(f"Label filling: added {added_total} SKILL spans "
              f"({len(vocabulary.known)} known skills; {len(vocabulary.blocked)} everyday words or "
              f"mostly-other-entity phrases left as labeled)")
    return data


def split(items: list, seed: int = SPLIT_SEED, dev_ratio: float = DEV_RATIO) -> tuple[list, list]:
    """Same split as NER_preparation.ipynb: seeded shuffle, last `dev_ratio` share is dev."""
    shuffled = list(items)
    random.Random(seed).shuffle(shuffled)
    usable = [item for item in shuffled if item_text(item).strip()]
    n_dev = min(max(1, round(len(usable) * dev_ratio)), len(usable) - 1) if len(usable) > 1 and dev_ratio > 0 else 0
    return usable[:len(usable) - n_dev], usable[len(usable) - n_dev:]
