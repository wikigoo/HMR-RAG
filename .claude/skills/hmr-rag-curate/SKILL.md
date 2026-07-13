---
name: hmr-rag-curate
description: Review the HMR-RAG knowledge corpus (wikigoo/HMR-RAG) for noise and errors after a crawl, then (re)write INDEX.md. Use when the user says "curate the RAG", "check the knowledge base", "review HMR-RAG", "clean the corpus", or after running the "Crawl sources" GitHub Action.
---

# HMR-RAG curate — quality review + index

Review the HMR (همر) knowledge corpus in **`wikigoo/HMR-RAG`**, flag noise/errors,
and regenerate **`INDEX.md`**. Read-only analysis + one written file (INDEX.md);
do not delete or rewrite corpus files unless the user explicitly asks.

## 1. Get the corpus

Prefer a local clone if present, else read from GitHub:

- Local: `D:\.HMR\HMR-RAG` (if it exists — fastest, use Glob/Read/Grep).
- Otherwise: `gh api repos/wikigoo/HMR-RAG/git/trees/main?recursive=1 --jq '.tree[]|select(.type=="blob")|.path'`
  then fetch files with `gh api repos/wikigoo/HMR-RAG/contents/<path> --jq '.content' | base64 -d`.

Corpus layout: `<brand>/<category>/<slug>.md`, each with YAML frontmatter
(`source`, `brand`, `category`, optional `model`, `crawled`).

## 2. Scan every markdown file for issues

Flag each file against these checks (report file path + the issue):

- **Noise / uncleaned scrape** — leftover boilerplate: `ADVERTISEMENT`, cookie/consent
  text, nav menus ("Skip to content", "Sign in", "Menu"), social-share blocks,
  "Related articles", footer junk, long runs of links.
- **Thin / failed** — body under ~200 chars, or crawl-error remnants (e.g. "404",
  "Access Denied", "captcha", empty after frontmatter).
- **Frontmatter** — missing/malformed; missing `source`, `brand`, or `category`;
  `brand` not in {apple, samsung, xiaomi, other}.
- **Casing drift** — brand folders are historically inconsistent (`Apple`,
  `samsung`, `Xiaomi`). Flag files whose folder casing is non-canonical so they
  can be normalised later (do not move them yourself unless asked).
- **Duplicates** — same `source` URL or same `model` appearing in multiple files.
- **Encoding / mojibake** — replacement chars (�) or broken Persian/UTF-8.

Prefer `Grep` for fast pattern sweeps (e.g. `ADVERTISEMENT`, `Skip to content`,
`�`), then Read suspicious files to confirm before flagging.

## 3. Write INDEX.md (at the repo root)

Produce/overwrite `INDEX.md` with:

1. **Summary** — total files, counts per brand and per category, crawl freshness
   (oldest/newest `crawled`), and totals per issue type.
2. **Catalog** — a table per brand: file path · model · category · source ·
   size · quality flags (✅ clean, or the issue tags found).
3. **Action list** — concrete cleanup items ranked by impact (e.g. "re-crawl these
   N thin files", "normalise Apple→apple casing", "dedupe X and Y", "add frontmatter
   to Z"), each with the exact file paths.

Write it in English (repo convention). Keep it deterministic so re-runs diff cleanly.

## 4. Report back

Summarise to the user: how many files scanned, how many clean vs flagged, the top
issues, and whether INDEX.md changed. If the user wants fixes applied (re-crawl,
casing normalise, dedupe, frontmatter), do them as a **separate PR** — corpus edits
are not automatic.

## Notes

- The corpus is fed into Flowise document stores (Apple/Samsung/Xiaomi) → embeddings
  → faiss. After curation the owner re-upserts changed docs (embed only what changed).
- Pairs with the crawl pipeline: `sources.yaml` + the "Crawl sources" GitHub Action.
- Never print secrets; this skill only reads public corpus content.
