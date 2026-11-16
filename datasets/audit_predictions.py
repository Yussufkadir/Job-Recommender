"""Judge the model's own SKILL predictions by hand: `python audit_predictions.py [--report]`.

The most direct precision check: no labels involved, just "is what the model marked a skill?"
Runs the model on the dev split (the CVs it never trained on) and shows a fixed random
sample of its SKILL predictions in context:

  y  correct: a skill, with sensible boundaries
  n  wrong: not a skill here (a job title, a company, a generic word) or badly cut
  s  skip    q  quit

Answers are saved to ner_eval/prediction_audit.csv after each one. Run from datasets/ with
the environment that has spacy and spacy-transformers (Job-Recommender-2).
"""
import argparse
from pathlib import Path

import spacy

from evaluate_ner import DEFAULT_MODEL, gold_doc
from ner_labels import item_id, item_spans, item_text, load_items, split
from review_auto_labels import AUDIT_PATH, DATASETS_DIR, read_reviews, report, review_loop


def model_predictions(model: Path) -> list[dict]:
    _, dev = split(load_items(str(DATASETS_DIR / "labeled_data.json")))
    blank = spacy.blank("en")
    texts = [gold_doc(blank, item_text(item), item_spans(item)).text for item in dev]
    nlp = spacy.load(model)
    predictions = []
    for item, doc in zip(dev, nlp.pipe(texts, batch_size=8)):
        for ent in doc.ents:
            if ent.label_ == "SKILL":
                predictions.append({"task_id": item_id(item), "start": ent.start_char, "end": ent.end_char,
                                    "text": ent.text, "_context": doc.text})
    return predictions


def main() -> None:
    parser = argparse.ArgumentParser(description="Judge a random sample of the model's SKILL predictions.")
    parser.add_argument("--sample", type=int, default=100, help="sample size (default 100)")
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--report", action="store_true", help="only print the precision so far")
    args = parser.parse_args()

    what = "Hand-checked precision"
    if args.report:
        report(read_reviews(AUDIT_PATH), what)
        return
    print(__doc__.split("\n\n")[2])
    print("Running the model on the dev CVs...")
    review_loop(model_predictions(args.model), AUDIT_PATH, args.sample,
                "Is the marked text a skill?", what)


if __name__ == "__main__":
    main()
