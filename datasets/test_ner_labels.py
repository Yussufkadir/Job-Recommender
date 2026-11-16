"""Run from datasets/: python -m pytest test_ner_labels.py (needs wordfreq)."""
import random

from ner_labels import build_vocabulary, fill_skill_spans, item_spans, item_text, propagate_labels, split
from review_auto_labels import wilson_interval


def task(text, *labeled, label="SKILL"):
    """A Label Studio-shaped task with the given phrases labeled (first occurrence of each)."""
    results = []
    for phrase in labeled:
        start = text.index(phrase)
        results.append({"value": {"start": start, "end": start + len(phrase), "labels": [label]}})
    return {"data": {"text": text}, "annotations": [{"result": results}]}


def filled(tasks, index):
    vocabulary = build_vocabulary(tasks)
    text = item_text(tasks[index])
    return [text[s:e] for s, e, _ in fill_skill_spans(text, item_spans(tasks[index]), vocabulary)]


def test_reads_label_studio_results():
    text = "python and sql"
    item = {"data": {"text": text}, "annotations": [{"result": [
        {"value": {"start": 0, "end": 6, "labels": ["SKILL"]}},
        {"value": {"start": 11, "end": 14, "labels": ["B-Skill"]}},
    ]}]}
    assert item_spans(item) == [(0, 6, "SKILL"), (11, 14, "SKILL")]


def test_fills_repeated_mentions_as_whole_words_only():
    tasks = [task("python here. pythonic is not python. cpython neither.", "python")]
    assert filled(tasks, 0) == ["python"]


def test_fills_skills_skipped_in_other_cvs():
    tasks = [task(f"cv {i}: docker and kubernetes", "docker") for i in range(3)]
    tasks.append(task("cv 3: we ship with docker daily")) 
    assert filled(tasks, 3) == ["docker"]


def test_does_not_fill_generic_words_that_were_rarely_labeled():
    tasks = [task(f"cv {i}: linux servers", "servers") for i in range(3)]
    tasks += [task(f"cv {i}: maintained servers") for i in range(3, 30)]  
    assert filled(tasks, 10) == []
    tasks[0] = task("linux servers, more servers", "servers")
    assert filled(tasks, 0) == ["servers"]


def test_does_not_fill_everyday_english_words():
    tasks = [task(f"cv {i}: rest apis", "rest") for i in range(5)]
    tasks.append(task("cv 5: took some rest"))
    assert filled(tasks, 5) == []


def test_does_not_fill_phrases_mostly_labeled_as_another_entity():
    tasks = [task(f"cv {i}: system administrator at acme", "system administrator", label="TITLE") for i in range(4)]
    tasks += [task(f"cv {i}: system administrator skills", "system administrator") for i in range(4, 7)]
    tasks.append(task("cv 7: system administrator"))
    assert filled(tasks, 7) == []


def test_longest_match_wins():
    tasks = [task(f"cv {i}: sql server and sql", "sql server", "and sql") for i in range(3)]
    tasks.append(task("cv 3: sql server dba"))
    assert filled(tasks, 3) == ["sql server"]


def test_propagate_labels_appends_spans_the_notebook_parser_reads():
    tasks = [task("python, python", "python")]
    propagate_labels(tasks, verbose=False)
    assert item_spans(tasks[0]) == [(0, 6, "SKILL"), (8, 14, "SKILL")]


def test_split_matches_the_notebook_shuffle():
    items = [{"text": f"cv {i}"} for i in range(10)]
    notebook_order = list(items)
    random.Random(23).shuffle(notebook_order)  
    train, dev = split(items)
    assert dev == notebook_order[8:] and train == notebook_order[:8]


def test_wilson_interval_brackets_the_observed_rate():
    low, high = wilson_interval(190, 200)
    assert low < 0.95 < high and high <= 1.0
