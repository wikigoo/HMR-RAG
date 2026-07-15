# Apple corpus

Knowledge documents for Apple devices, feeding the **Apple** Flowise document store.

## Contents (2026-07-14)

| Folder | Files | What it is |
|--------|------:|------------|
| `specs/` | 47 | Device spec pages (gsmarena), YAML frontmatter |
| `howto/` | 91 | Apple Support how-to / troubleshooting articles |
| `chunks/` | 619 | Pre-chunked Apple Support articles |
| **Total** | **757** | |

## Provenance & format ⚠️

Unlike `samsung/` and `Xiaomi/`, most of this folder is **not** produced by the
`sources.yaml` + `crawl.py` pipeline. The 619 files in `chunks/` and the 91 in
`howto/` are a **legacy bulk import from Apple Support** and do **not** carry YAML
frontmatter. They begin with a line like:

```
[Source: apple_support] [Title: How to add an AirTag to Find My - Apple Support]
```

Only `specs/` (and one page) follow the standard `source/brand/category/model/crawled`
YAML frontmatter used everywhere else in the corpus.

### Consequences
- The curate skill flags all 710 non-YAML files as "missing frontmatter" — this is
  the single largest quality item in the corpus (see [`INDEX.md`](../INDEX.md)).
- Some `chunks/` files are thin (headers + `ADVERTISEMENT` only) and are cleanup
  candidates, not real content.

## Adding Apple content

New Apple sources go through the normal pipeline: add to [`sources.yaml`](../sources.yaml)
with `brand: apple`, then run **Actions → Crawl sources** (optionally `only_brand=apple`).
New crawled files land in `specs/` or `howto/` **with** proper frontmatter. Do not
hand-edit the legacy `chunks/` files; if the apple_support set is ever re-imported,
regenerate it rather than patching individual chunks.
