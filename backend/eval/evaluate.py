"""Score every ranking variant on the golden queries: `python -m eval.evaluate [--per-query] [--save]`.

Prints Precision@10, NDCG@10 and MRR per variant (averaged over judged queries), plus how
much of each top 10 is judged. --save stores the numbers in eval/results/ with the git
commit, and every run compares against the most recent saved result.
"""
import argparse
import json
import subprocess
from datetime import datetime, timezone
from statistics import mean

from eval.common import (
    BACKEND_DIR, K, RESULTS_DIR, SNAPSHOT_PATH, VARIANTS, Runner, grades_by_query, load_queries,
    open_snapshot, read_judgment_rows,
)
from eval.metrics import judged_at_k, ndcg_at_k, precision_at_k, reciprocal_rank

PRODUCTION_VARIANT = "hybrid"
LOW_JUDGED_WARNING = 0.9


def git_commit() -> str:
    try:
        sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=BACKEND_DIR,
                             capture_output=True, text=True, check=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain"], cwd=BACKEND_DIR,
                               capture_output=True, text=True, check=True).stdout.strip()
        return f"{sha}{'-dirty' if dirty else ''}"
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def latest_saved() -> dict | None:
    files = sorted(RESULTS_DIR.glob("*.json"))
    return json.loads(files[-1].read_text()) if files else None


def fmt(value: float | None) -> str:
    return "  n/a" if value is None else f"{value:5.3f}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Score ranking variants on the golden queries.")
    parser.add_argument("--per-query", action="store_true", help="also print NDCG@10 per query")
    parser.add_argument("--save", action="store_true", help="save results to eval/results/")
    args = parser.parse_args()

    queries = load_queries()
    grades = grades_by_query(read_judgment_rows())
    judged_queries = [query for query in queries if grades.get(query.id)]
    if not judged_queries:
        raise SystemExit("No judgments yet. Label some results first: python -m eval.label")

    db = open_snapshot()
    runner = Runner(db)
    snapshot_date = datetime.fromtimestamp(runner.now, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"Snapshot: {SNAPSHOT_PATH.name} (taken {snapshot_date})   "
          f"Queries judged: {len(judged_queries)}/{len(queries)}   "
          f"Judgments: {sum(len(g) for g in grades.values())}")

    results: dict[str, dict] = {}
    per_query: dict[str, dict[str, float | None]] = {}
    for variant in VARIANTS:
        scores = {"p": [], "ndcg": [], "mrr": [], "judged": []}
        available = True
        for query in judged_queries:
            run = runner.run(query, variant)
            if not run.available:
                available = False
                break
            query_grades = grades[query.id]
            scores["p"].append(precision_at_k(run.job_keys, query_grades, K))
            scores["mrr"].append(reciprocal_rank(run.job_keys, query_grades, K))
            scores["judged"].append(judged_at_k(run.job_keys, query_grades, K))
            ndcg = ndcg_at_k(run.job_keys, query_grades, K)
            per_query.setdefault(query.id, {})[variant] = ndcg
            if ndcg is not None:
                scores["ndcg"].append(ndcg)
        results[variant] = {
            "available": available,
            "precision_at_10": mean(scores["p"]) if available else None,
            "ndcg_at_10": mean(scores["ndcg"]) if available and scores["ndcg"] else None,
            "mrr": mean(scores["mrr"]) if available else None,
            "judged_at_10": mean(scores["judged"]) if available else None,
        }

    previous = latest_saved()
    print()
    print(f"{'variant':<22}{'P@10':>7}{'NDCG@10':>9}{'MRR':>7}{'judged@10':>11}   vs last saved (NDCG@10)")
    for variant, metrics in results.items():
        marker = " *" if variant == PRODUCTION_VARIANT else ""
        if not metrics["available"]:
            print(f"{variant + marker:<22}   unavailable: the recommender couldn't provide this signal")
            continue
        delta = ""
        old = (previous or {}).get("variants", {}).get(variant, {}).get("ndcg_at_10")
        if old is not None and metrics["ndcg_at_10"] is not None:
            delta = f"{metrics['ndcg_at_10'] - old:+.3f} (was {old:.3f})"
        judged_note = "  <- judge new results" if metrics["judged_at_10"] < LOW_JUDGED_WARNING else ""
        print(f"{variant + marker:<22}{fmt(metrics['precision_at_10']):>7}{fmt(metrics['ndcg_at_10']):>9}"
              f"{fmt(metrics['mrr']):>7}{metrics['judged_at_10']:>10.0%}   {delta}{judged_note}")
    print(f"\n* = what production uses. Results nobody judged count as not relevant; "
          f"if judged@10 is below {LOW_JUDGED_WARNING:.0%}, run python -m eval.label.")

    if args.per_query:
        variants = [v for v in VARIANTS if results[v]["available"]]
        print(f"\nNDCG@10 per query\n{'query':<20}" + "".join(f"{v[:12]:>13}" for v in variants))
        for query in judged_queries:
            print(f"{query.id:<20}" + "".join(f"{fmt(per_query[query.id].get(v)):>13}" for v in variants))

    if args.save:
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S")
        path = RESULTS_DIR / f"{stamp}.json"
        path.write_text(json.dumps({
            "saved_at": stamp,
            "git_commit": git_commit(),
            "snapshot_taken": snapshot_date,
            "queries_judged": len(judged_queries),
            "judgments": sum(len(g) for g in grades.values()),
            "variants": results,
            "per_query_ndcg_at_10": per_query,
        }, indent=2))
        print(f"\nSaved to {path.relative_to(BACKEND_DIR)}")


if __name__ == "__main__":
    main()
