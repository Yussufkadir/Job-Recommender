"""Report NER metrics on the held-out dev split: `python evaluate_ner.py [--model PATH] [--save]`.

Run from datasets/ with an environment that has spacy, spacy-transformers and wordfreq
(the recommender service's, plus wordfreq). Rebuilds the same dev split as
NER_preparation.ipynb (seed 23, last 20%) and scores the model three ways:

  as annotated      against the labels exactly as annotated: what spaCy reported during
                    training. Understates precision, because skills that were skipped
                    while labeling count as false positives when the model finds them.
  filled            against labels with skipped skills filled in (ner_labels.py).
  filled, overlap   as above, but a prediction that overlaps a gold span counts
                    ("django 1.8" vs "django"), for boundary-insensitive numbers.

The filled numbers are only as good as the filling: review_auto_labels.py measures that,
and its accuracy is printed alongside.
"""
import argparse
import json
from collections import defaultdict
from pathlib import Path

import spacy
from spacy.tokens import Doc
from spacy.util import filter_spans

from ner_labels import (
    DEV_RATIO, SPLIT_SEED, build_vocabulary, fill_skill_spans, item_spans, item_text, load_items, split,
)
from review_auto_labels import AUDIT_PATH, REVIEW_PATH, read_reviews, summarize

DATASETS_DIR = Path(__file__).resolve().parent
DEFAULT_MODEL = DATASETS_DIR.parent / "ml_services/recommender_service/transformer-models/model-best"
METRICS_PATH = DATASETS_DIR / "ner_eval" / "ner_metrics.json"


def gold_doc(nlp_blank, text: str, spans) -> Doc:
    """Gold spans the way NER_preparation.ipynb builds training docs: token-aligned only,
    no spans with surrounding whitespace, overlaps resolved by filter_spans."""
    doc = nlp_blank.make_doc(text)
    kept = []
    for start, end, label in spans:
        span = doc.char_span(start, end, label=label)
        if span is not None and span.text.strip() == span.text:
            kept.append(span)
    doc.ents = filter_spans(kept)
    return doc


class Counts:
    def __init__(self):
        self.tp = self.fp = self.fn = 0

    def add(self, gold: set, predicted: set) -> None:
        self.tp += len(gold & predicted)
        self.fp += len(predicted - gold)
        self.fn += len(gold - predicted)

    def scores(self) -> dict:
        p = self.tp / (self.tp + self.fp) if self.tp + self.fp else 0.0
        r = self.tp / (self.tp + self.fn) if self.tp + self.fn else 0.0
        f = 2 * p * r / (p + r) if p + r else 0.0
        return {"precision": round(p, 3), "recall": round(r, 3), "f1": round(f, 3), "support": self.tp + self.fn}


def overlap_scores(gold_spans: list[set], predicted_spans: list[set]) -> dict:
    """Precision: predictions overlapping some gold span; recall: gold spans overlapping some prediction."""
    def overlaps(span, others):
        return any(span[0] < o[1] and span[1] > o[0] for o in others)
    hit_p = sum(overlaps(p, g) for g, ps in zip(gold_spans, predicted_spans) for p in ps)
    n_p = sum(len(ps) for ps in predicted_spans)
    hit_g = sum(overlaps(x, ps) for g, ps in zip(gold_spans, predicted_spans) for x in g)
    n_g = sum(len(g) for g in gold_spans)
    p, r = (hit_p / n_p if n_p else 0.0), (hit_g / n_g if n_g else 0.0)
    return {"precision": round(p, 3), "recall": round(r, 3), "f1": round(2 * p * r / (p + r) if p + r else 0.0, 3),
            "support": n_g}


def main() -> None:
    parser = argparse.ArgumentParser(description="Report NER metrics on the dev split.")
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--data", type=Path, default=DATASETS_DIR / "labeled_data.json")
    parser.add_argument("--save", action="store_true", help=f"write the metrics to {METRICS_PATH.relative_to(DATASETS_DIR)}")
    args = parser.parse_args()

    items = load_items(str(args.data))
    vocabulary = build_vocabulary(items)  # from all data, as the notebook fills labels before splitting
    _, dev = split(items)
    print(f"Dev split: {len(dev)} CVs (seed {SPLIT_SEED}, {DEV_RATIO:.0%} of {len(items)})  Model: {args.model}")

    blank = spacy.blank("en")
    annotated_docs, filled_skill_spans = [], []
    added = 0
    for item in dev:
        text, spans = item_text(item), item_spans(item)
        doc = gold_doc(blank, text, spans)
        annotated_docs.append(doc)
        extra = fill_skill_spans(text, [(e.start_char, e.end_char, e.label_) for e in doc.ents], vocabulary)
        added += len(extra)
        skill_spans = {(e.start_char, e.end_char) for e in doc.ents if e.label_ == "SKILL"}
        filled_skill_spans.append(skill_spans | {
            (e.start_char, e.end_char) for e in gold_doc(blank, text, extra).ents
        })

    nlp = spacy.load(args.model)
    per_label = defaultdict(Counts)
    filled = Counts()
    predicted_skills = []
    for gold, pred in zip(annotated_docs, nlp.pipe([d.text for d in annotated_docs], batch_size=8)):
        for label in {e.label_ for e in gold.ents} | {e.label_ for e in pred.ents}:
            per_label[label].add({(e.start_char, e.end_char) for e in gold.ents if e.label_ == label},
                                 {(e.start_char, e.end_char) for e in pred.ents if e.label_ == label})
        predicted_skills.append({(e.start_char, e.end_char) for e in pred.ents if e.label_ == "SKILL"})
    for gold_spans, predicted in zip(filled_skill_spans, predicted_skills):
        filled.add(gold_spans, predicted)

    annotated_skill_total = per_label["SKILL"].tp + per_label["SKILL"].fn
    results = {
        "model": str(args.model),
        "dev_docs": len(dev),
        "skill_spans_annotated": annotated_skill_total,
        "skill_spans_added_by_filling": added,
        "as_annotated": {label: counts.scores() for label, counts in sorted(per_label.items())},
        "skill_filled": filled.scores(),
        "skill_filled_overlap": overlap_scores(filled_skill_spans, predicted_skills),
    }
    for key, path in (("auto_label_review", REVIEW_PATH), ("prediction_audit", AUDIT_PATH)):
        summary = summarize(read_reviews(path))
        if summary:
            results[key] = {k: v for k, v in summary.items() if k != "marked_wrong"}

    print(f"\nSKILL mentions in dev: {annotated_skill_total} annotated + {added} added by filling "
          f"({added / max(annotated_skill_total + added, 1):.0%} were unlabeled)")
    header = f"{'':<30}{'precision':>10}{'recall':>9}{'F1':>8}{'support':>9}"

    def print_row(name, s):
        print(f"{name:<30}{s['precision']:>10.3f}{s['recall']:>9.3f}{s['f1']:>8.3f}{s['support']:>9}")

    print("\nAgainst your labels as annotated (partial, so SKILL precision is understated):")
    print(header)
    for label, scores in results["as_annotated"].items():
        print_row(label, scores)
    print("\nAgainst labels with skipped skills filled in (the numbers to report):")
    print(header)
    print_row("SKILL", results["skill_filled"])
    print_row("SKILL, overlap counts", results["skill_filled_overlap"])

    print("\nChecked by hand:")
    for key, title, script in (("auto_label_review", "filled labels correct", "review_auto_labels.py"),
                               ("prediction_audit", "model predictions correct (precision)", "audit_predictions.py")):
        check = results.get(key)
        if check:
            print(f"  {title}: {check['accuracy']:.1%} of {check['reviewed']} "
                  f"(95% CI {check['ci95'][0]:.1%}-{check['ci95'][1]:.1%})")
        else:
            print(f"  {title}: not done yet, run python {script}")

    if args.save:
        METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
        METRICS_PATH.write_text(json.dumps(results, indent=2))
        print(f"Saved to {METRICS_PATH.relative_to(DATASETS_DIR)}")


if __name__ == "__main__":
    main()
