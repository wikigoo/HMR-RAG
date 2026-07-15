# Samsung corpus

Knowledge documents for Samsung devices, feeding the **Samsung** Flowise document store.

## Contents (2026-07-14)

| Folder | Files | What it is |
|--------|------:|------------|
| `specs/` | 29 | Device spec pages (gsmarena), YAML frontmatter |
| `howto/` | 21 | Official samsung.com support / troubleshooting articles |
| **Total** | **50** | (crawled via the pipeline) |

Plus two legacy root files that predate the pipeline:
- `Samsung Galaxy.md` — a ~144 KB Wikipedia dump with a different frontmatter
  shape (`title`/`source`/`author`) and a space in its filename. Flagged for
  normalisation; do not treat it as a model page.
- `README.md` — this file.

## Provenance & format

Everything under `specs/` and `howto/` is produced by the `sources.yaml` +
`crawl.py` pipeline and carries standard YAML frontmatter
(`source`, `brand: samsung`, `category`, `model`, `crawled`).

- **specs** come from gsmarena, weighted toward the mid-range/budget models that
  actually sell in Iran (Galaxy A / M series) plus the S flagships.
- **howto** come from `samsung.com/us/support/*` (with two `uk` pages that have no
  US equivalent). Regional mirrors are deliberately avoided — they carry the same
  articles under different slugs and would create near-duplicates.
- `answer/ANS10002504` (IMEI / serial lookup) serves the used-phone + counterfeit
  detection pillar.

## Adding Samsung content

Add entries to [`sources.yaml`](../sources.yaml) with `brand: samsung`, verify each
URL returns HTTP 200 first, then run **Actions → Crawl sources** with
`only_brand=samsung`. gsmarena is rate-limited (~1 req / 15-20s) and the crawler
throttles per host, so a specs sweep takes several minutes.
