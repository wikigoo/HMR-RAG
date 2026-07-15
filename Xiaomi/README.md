# Xiaomi corpus

Knowledge documents for Xiaomi devices, feeding the **Xiaomi** Flowise document store.

## Contents (2026-07-14)

| Folder | Files | What it is |
|--------|------:|------------|
| `specs/` | 30 | Device spec pages (gsmarena), YAML frontmatter |
| `howto/` | 26 | Official mi.com global support / FAQ articles |
| **Total** | **56** | (crawled via the pipeline) |

Plus one legacy root file:
- `Xiaomi.md` — a ~126 KB Wikipedia dump with a non-standard frontmatter shape.
  Flagged for normalisation; not a model page.

## Provenance & format

Everything under `specs/` and `howto/` is produced by the `sources.yaml` +
`crawl.py` pipeline and carries standard YAML frontmatter
(`source`, `brand: xiaomi`, `category`, `model`, `crawled`).

- **specs** come from gsmarena and cover the lines that matter in Iran: Redmi Note,
  the Redmi budget A/C line, POCO, and the numbered flagship line.
- **howto** come from `mi.com/global/support/*`. These pages render their body
  **client-side**, so `crawl.py` uses a post-load paint delay
  (`delay_before_return_html`) to capture them — without it they came back as empty
  17-char shells. Do **not** switch that to `wait_until="networkidle"`: these pages
  keep analytics sockets open, the network never idles, and every page times out
  (a run tried it and fell from 41 successes to 26).
- `guidance/imei_smartphone` serves the used-phone + counterfeit-detection pillar.

### Known exclusions
- `mi.com/verify` (official product authentication) is **not** crawled — it sits
  behind Akamai bot protection and fails every run. Do not re-add it without
  confirming it actually crawls.
- `mi.com/global/support/article/KA-03581/` crawls THIN (~158 chars, upstream stub)
  and is a removal candidate from `sources.yaml`.

## ⚠️ Flowise state
The Xiaomi document store currently has **0 chunks** and is stuck `SYNCING` because
its loader still points at the deleted `wikigoo/Xiaomi` repo (see the caveat in the
[root README](../README.md)). This corpus will not reach the bot until that loader
is repointed at `HMR-RAG` and re-upserted.

## Adding Xiaomi content

Add entries to [`sources.yaml`](../sources.yaml) with `brand: xiaomi`, verify each
URL returns HTTP 200 first, then run **Actions → Crawl sources** with
`only_brand=xiaomi`.
