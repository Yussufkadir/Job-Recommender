# Ranking evaluation

Measures how good job search results are, as numbers that can be compared across
versions of the ranking code. Run everything from `backend/`.

## The three steps

```bash
python -m eval.snapshot     # 1. freeze the current job index (once, or when you want fresh data)
python -m eval.label        # 2. judge results as relevant or not (resumable, quit any time)
python -m eval.evaluate     # 3. print the metrics for every ranking variant
```

The recommender service must be running (`RECOMMENDER_URL`, with `sentence-transformers`
installed) for the skills and semantic variants; without it they're reported as unavailable.

### 1. Snapshot

`eval/snapshots/jobs.db` is a frozen copy of the job index. The live index changes every
collection run, so measuring against it would move the numbers for reasons unrelated to
the code. The snapshot also gets any missing skills and embeddings filled in, and the
evaluation pins "now" to the moment it was taken, so job ages don't drift either.

Snapshots are large and not committed (see `.gitignore`). Judgments refer to jobs by
`source:external_id`, so after taking a new snapshot most of them still apply; run
`eval.label` to judge whatever is new in the top results.

### 2. Labeling

`queries.json` holds the golden queries: realistic searches with a title, skills,
countries and seniority. For each query, the top 10 results of every variant are merged
into `judgments.csv`, and `eval.label` walks you through the ones without a grade:

| Grade | Meaning |
|---|---|
| 2 | Strong match: you'd apply with this profile |
| 1 | Partly relevant: right field, but off on level, stack or focus |
| 0 | Not relevant |

Judge the job against the query's profile, not your own. Be consistent rather than
perfect: the numbers are for comparing variants, and a consistent judge compares fairly.
You can also edit the `relevance` column in `judgments.csv` directly.

### 3. Metrics

| Metric | Question it answers |
|---|---|
| Precision@10 | How many of the top 10 are relevant (grade 1 or 2)? |
| NDCG@10 | Are the best jobs near the top? Uses the 0/1/2 grades; 1.0 is the ideal order. |
| MRR | How far down is the first relevant job? 1.0 = first result, 0.5 = second. |
| judged@10 | How much of the top 10 has a grade. Unjudged results count as not relevant. |

Variants (weights in `common.py`): each signal alone, `title+keywords`, the hybrid
without description similarity, and `hybrid`, which is what production uses.

`--per-query` shows NDCG@10 for each query; `--save` stores the run in `eval/results/`
with the git commit. Each run compares against the latest saved result, which gives
statements like "adding description similarity raised NDCG@10 from 0.61 to 0.74".

## Adding queries

Add an entry to `queries.json` with a new `id`, then run `python -m eval.label` to
judge its results. More queries make the numbers steadier; 15-30 is a good range.
