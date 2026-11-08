"""Check the automatically filled SKILL labels by hand: `python review_auto_labels.py [--report]`.

Shows a fixed random sample of auto-added labels, one at a time, in context:

  y  correct: this is a skill, with the right boundaries
  n  wrong: not a skill here, or cut in the wrong place ("java" in "java script")
  s  skip    q  quit

Answers are saved after each one to ner_eval/auto_label_review.csv, so you can stop and
resume. The accuracy (with a 95% confidence interval) shows whether the filled-in labels,
and the metrics computed on them, can be trusted. Run from datasets/; needs wordfreq.
The review loop here is shared with audit_predictions.py.
"""
import argparse
import csv
import math
import random
from pathlib import Path

from ner_labels import build_vocabulary, fill_skill_spans, item_id, item_spans, item_text, load_items

DATASETS_DIR = Path(__file__).resolve().parent
REVIEW_PATH = DATASETS_DIR / "ner_eval" / "auto_label_review.csv"
AUDIT_PATH = DATASETS_DIR / "ner_eval" / "prediction_audit.csv"  # written by audit_predictions.py
SAMPLE_SEED = 2024
CONTEXT_CHARS = 90
FIELDS = ["task_id", "start", "end", "text", "correct"]


def wilson_interval(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    """95% confidence interval for a proportion; reliable for small samples and rates near 1."""
    if total == 0:
        return 0.0, 0.0
    p = successes / total
    centre = (p + z * z / (2 * total)) / (1 + z * z / total)
    margin = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / (1 + z * z / total)
    return max(0.0, centre - margin), min(1.0, centre + margin)


def read_reviews(path: Path = REVIEW_PATH) -> dict[tuple, dict]:
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as handle:
        return {(row["task_id"], int(row["start"]), int(row["end"])): row for row in csv.DictReader(handle)}


def write_reviews(path: Path, reviews: dict[tuple, dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows({key: row[key] for key in FIELDS} for row in reviews.values())
    tmp.replace(path) 


def summarize(reviews: dict[tuple, dict]) -> dict | None:
    answered = [row for row in reviews.values() if row["correct"] in ("y", "n")]
    if not answered:
        return None
    correct = sum(row["correct"] == "y" for row in answered)
    low, high = wilson_interval(correct, len(answered))
    return {"reviewed": len(answered), "correct": correct, "accuracy": round(correct / len(answered), 3),
            "ci95": [round(low, 3), round(high, 3)],
            "marked_wrong": [row["text"] for row in answered if row["correct"] == "n"]}


def report(reviews: dict[tuple, dict], what: str) -> None:
    summary = summarize(reviews)
    if summary is None:
        print("No answers yet.")
        return
    print(f"{what}: {summary['correct']}/{summary['reviewed']} = {summary['accuracy']:.1%} "
          f"(95% CI {summary['ci95'][0]:.1%}-{summary['ci95'][1]:.1%})")
    if summary["marked_wrong"]:
        print("Marked wrong:", ", ".join(summary["marked_wrong"]))


def review_loop(candidates: list[dict], path: Path, sample_size: int, question: str, what: str) -> None:
    """Ask about a fixed random sample of candidates ({task_id, start, end, text, _context});
    answers already saved in `path` are skipped, so a session can be resumed."""
    reviews = read_reviews(path)
    candidates = sorted(candidates, key=lambda c: (c["task_id"], c["start"]))
    sample = random.Random(SAMPLE_SEED).sample(candidates, min(sample_size, len(candidates)))
    pending = [c for c in sample
               if reviews.get((c["task_id"], c["start"], c["end"]), {}).get("correct") not in ("y", "n")]
    print(f"{len(candidates)} candidates; checking a fixed sample of {len(sample)} ({len(pending)} left).")
    try:
        for position, candidate in enumerate(pending, start=1):
            text, start, end = candidate["_context"], candidate["start"], candidate["end"]
            left = " ".join(text[max(0, start - CONTEXT_CHARS):start].split())
            right = " ".join(text[end:end + CONTEXT_CHARS].split())
            print(f"\n[{position}/{len(pending)}]  ...{left} >>>{text[start:end]}<<< {right}...")
            answer = ""
            while answer not in ("y", "n", "s", "q"):
                answer = input(f"{question} [y/n], s = skip, q = quit: ").strip().lower()
            if answer == "q":
                break
            if answer == "s":
                continue
            reviews[(candidate["task_id"], start, end)] = {**candidate, "correct": answer}
            write_reviews(path, reviews)
    except (KeyboardInterrupt, EOFError):
        print("\nStopped. Everything answered so far is saved.")
    print()
    report(reviews, what)


def auto_labels(items) -> list[dict]:
    vocabulary = build_vocabulary(items)
    labels = []
    for item in items:
        text = item_text(item)
        for start, end, _ in fill_skill_spans(text, item_spans(item), vocabulary):
            labels.append({"task_id": item_id(item), "start": start, "end": end, "text": text[start:end],
                           "_context": text})
    return labels


def main() -> None:
    parser = argparse.ArgumentParser(description="Review a random sample of automatically filled SKILL labels.")
    parser.add_argument("--sample", type=int, default=200, help="sample size (default 200)")
    parser.add_argument("--report", action="store_true", help="only print the accuracy so far")
    args = parser.parse_args()

    what = "Auto-label accuracy"
    if args.report:
        report(read_reviews(), what)
        return
    print(__doc__.split("\n\n")[1])
    labels = auto_labels(load_items(str(DATASETS_DIR / "labeled_data.json")))
    review_loop(labels, REVIEW_PATH, args.sample, "Is the marked text a skill?", what)


if __name__ == "__main__":
    main()
