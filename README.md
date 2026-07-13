# HMR-RAG

The **source-of-truth knowledge corpus** for HMR (همر) — the Iranian mobile-hardware
advisor. Curated markdown, versioned in git, organised by brand. Flowise document
stores ingest from here, embed with `text-embedding-3-large`, and serve the RAG on
the VPS (faiss).

```
Sources (gsmarena, support pages, price refs, registry, …)
   │   GitHub Action "Crawl sources" (manual) → crawl4AI → clean markdown
   ▼
HMR-RAG  (this repo — source of truth, versioned markdown by brand)
   │   ├─ Claude skill `hmr-rag-curate`: review noise/errors, write INDEX.md
   │   on change → Flowise upsert (embed only changed docs)
   ▼
Flowise document stores (Apple / Samsung / Xiaomi) → embeddings → faiss (VPS)
```

## Layout

```
Apple/    samsung/    Xiaomi/       ← per brand (casing is historically inconsistent)
  specs/     …/         …/           ← gsmarena specs
  howto/                             ← support / how-to guides
  <category>/                        ← price | registry | other
sources.yaml                         ← crawl manifest (edit by hand)
scripts/crawl.py                     ← crawl4AI runner
scripts/requirements.txt
.github/workflows/crawl.yml          ← "Crawl sources" (manual trigger)
INDEX.md                             ← written by the hmr-rag-curate skill
```

Each markdown file carries YAML frontmatter: `source`, `brand`, `category`,
optional `model`, and `crawled` timestamp.

## Add / remove / update content

1. **Edit `sources.yaml`** — add or remove entries (`url`, `brand`, `category`,
   optional `model`). This file is the only thing you hand-edit for crawling.
2. **Run the crawler:** GitHub → **Actions → Crawl sources → Run workflow**
   (optionally limit to one brand). It fetches each URL, produces cleaned
   markdown at `<brand>/<category>/<slug>.md`, and commits the changes.
   *Crawling is manual only — nothing runs on a schedule.*
3. **Re-running a source overwrites its file** with a fresh crawl.

You can also add curated markdown by hand (same frontmatter) without a source URL.

## Review quality (Claude skill)

Run the **`hmr-rag-curate`** skill to scan the corpus for noise and errors
(leftover ad/nav text, thin or failed pages, missing frontmatter, brand-folder
casing drift, duplicates) and to (re)generate **`INDEX.md`** — a catalog of the
corpus with per-file quality flags. Use it after each crawl before re-upserting
to Flowise.

## Feeding Flowise

After the corpus changes, re-upsert the affected document store(s) in Flowise so
only changed docs are re-embedded (embedding cost control). See the Document
Stores guide in HMR-Book.
