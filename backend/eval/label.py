"""Label search results as relevant or not: `python -m eval.label [--query ID] [--pool-only]`.

For every golden query, the top 10 results of every ranking variant are pooled (merged,
duplicates removed) into eval/judgments.csv. Then you judge each pooled job once:

  2  strong match: you'd apply with this profile
  1  partly relevant: right field, but off on level, stack or focus
  0  not relevant

Answers are saved immediately, so you can quit (q) and resume any time. Run it again
after changing the ranking: only jobs that newly reach a top 10 need judging.
The CSV can also be edited by hand (the relevance column).
"""
import argparse
import json
import textwrap
import webbrowser

from eval.common import (
    K, VARIANTS, Runner, load_queries, open_snapshot, read_judgment_rows, write_judgment_rows,
)
from app.models.job_posting import JobPosting  # noqa: E402

DESCRIPTION_PREVIEW_CHARS = 700


def build_pool(runner: Runner, queries) -> list[dict]:
    """Add every job that reaches a variant's top K to the judgments file, unjudged."""
    rows = read_judgment_rows()
    known = {(row["query_id"], row["job_key"]) for row in rows}
    added = 0
    for query in queries:
        for variant in VARIANTS:
            run = runner.run(query, variant)
            if not run.available:
                continue
            for key, job in zip(run.job_keys, run.jobs):
                if (query.id, key) in known:
                    continue
                known.add((query.id, key))
                rows.append({
                    "query_id": query.id, "job_key": key, "relevance": "",
                    "title": job["title"], "company": job["company"],
                    "location": job["location"] or "", "link": job["link"],
                })
                added += 1
    write_judgment_rows(rows)
    print(f"Pool updated: {added} new results to judge ({len(rows)} in total).")
    return rows


def show(job: JobPosting, row: dict, position: int, remaining: int) -> None:
    skills = ", ".join(json.loads(job.skills or "[]")) or "none found"
    description = textwrap.fill(" ".join(job.description.split())[:DESCRIPTION_PREVIEW_CHARS], width=100)
    print("\n" + "-" * 100)
    print(f"[{position}, {remaining} left]  {job.title}")
    print(f"{job.company}  |  {job.location or row['location']}  |  {job.source}"
          f"{'  |  remote' if job.remote else ''}  |  level: {job.seniority}")
    print(f"Skills: {skills}")
    print(description + "...")


def label(runner: Runner, queries, only: str | None) -> None:
    rows = read_judgment_rows()
    by_id = {query.id: query for query in queries}
    pending = [row for row in rows if not (row.get("relevance") or "").strip()
               and row["query_id"] in by_id and (only is None or row["query_id"] == only)]
    if not pending:
        print("Nothing left to judge.")
        return

    print(__doc__.split("\n\n")[2])  # the relevance scale
    current_query = None
    for position, row in enumerate(pending, start=1):
        query = by_id[row["query_id"]]
        if query.id != current_query:
            current_query = query.id
            print("\n" + "=" * 100)
            print(f"QUERY {query.id}: \"{query.query}\"  skills: {', '.join(query.skills)}  "
                  f"countries: {', '.join(query.countries)}  level: {query.seniority}")

        job = runner.db.query(JobPosting).filter_by(
            source=row["job_key"].split(":", 1)[0], external_id=row["job_key"].split(":", 1)[1]
        ).first()
        if job is None:
            print(f"\n(skipping {row['job_key']}: not in this snapshot)")
            continue
        show(job, row, position, len(pending) - position)

        while True:
            answer = input("Relevance [2/1/0], o = open link, s = skip, q = quit: ").strip().lower()
            if answer == "o":
                webbrowser.open(job.url)
            elif answer in {"0", "1", "2", "s", "q"}:
                break
        if answer == "q":
            break
        if answer == "s":
            continue
        row["relevance"] = answer
        write_judgment_rows(rows)

    judged = sum(1 for row in rows if (row.get("relevance") or "").strip())
    print(f"\nSaved. {judged}/{len(rows)} results judged.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Label search results for the ranking evaluation.")
    parser.add_argument("--query", help="only judge this query id")
    parser.add_argument("--pool-only", action="store_true", help="update the pool, don't start labeling")
    args = parser.parse_args()

    queries = load_queries()
    runner = Runner(open_snapshot())
    print(f"Pooling the top {K} of {len(VARIANTS)} variants for {len(queries)} queries...")
    build_pool(runner, queries)
    if not args.pool_only:
        try:
            label(runner, queries, args.query)
        except (KeyboardInterrupt, EOFError):
            print("\nStopped. Everything answered so far is saved.")


if __name__ == "__main__":
    main()
