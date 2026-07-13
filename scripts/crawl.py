#!/usr/bin/env python3
"""Crawl the sources listed in ../sources.yaml into cleaned markdown.

Each source becomes  <brand>/<category>/<slug>.md  with YAML frontmatter.
Run via the "Crawl sources" GitHub Action (manual trigger). Individual source
failures are logged and skipped — they never fail the whole run.
"""
import asyncio
import os
import re
import sys
from datetime import datetime, timezone

import yaml
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES_FILE = os.path.join(ROOT, "sources.yaml")

# Manifest brand -> on-disk folder. Casing is historically inconsistent
# (Apple / samsung / Xiaomi); this keeps new files with the existing content.
BRAND_DIRS = {"apple": "Apple", "samsung": "samsung", "xiaomi": "Xiaomi", "other": "other"}


def slugify(url: str) -> str:
    s = re.sub(r"^https?://", "", url.strip())
    s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()
    return s[:90] or "page"


# Residual boilerplate lines to drop after crawl4AI's own filtering. Only
# applied to short lines so real prose that happens to contain a word is kept.
_NOISE = re.compile(
    r"(^ADVERTISEMENT$"
    r"|Become a fan"
    r"|\d[\d,]*\s*hits"
    r"|Skip to (?:main )?content"
    r"|\bSign in\b|\bLog in\b"
    r"|Accept.*cookies|cookie policy|consent"
    r"|Follow us on|Share on (?:Facebook|Twitter|X|WhatsApp|Telegram))",
    re.IGNORECASE,
)


def clean_markdown(md: str) -> str:
    kept = []
    for line in md.splitlines():
        s = line.strip()
        if s and len(s) < 120 and _NOISE.search(s):
            continue
        kept.append(line.rstrip())
    text = "\n".join(kept)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def frontmatter(src: dict) -> str:
    lines = [
        "---",
        f"source: {src['url']}",
        f"brand: {src['brand']}",
        f"category: {src['category']}",
    ]
    if src.get("model"):
        lines.append(f"model: {src['model']}")
    lines.append(f"crawled: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}")
    lines.append("---\n\n")
    return "\n".join(lines)


async def main() -> int:
    with open(SOURCES_FILE, encoding="utf-8") as fh:
        manifest = yaml.safe_load(fh) or {}
    sources = manifest.get("sources") or []

    only = os.environ.get("ONLY_BRAND", "all").strip().lower()
    if only and only != "all":
        sources = [s for s in sources if str(s.get("brand", "")).lower() == only]

    if not sources:
        print("No sources to crawl.")
        return 0

    browser_cfg = BrowserConfig(headless=True, verbose=False)
    run_cfg = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        excluded_tags=["nav", "header", "footer", "aside", "form", "script", "style"],
        exclude_external_links=True,
        exclude_social_media_links=True,
        remove_overlay_elements=True,
        word_count_threshold=5,
        markdown_generator=DefaultMarkdownGenerator(
            content_filter=PruningContentFilter(
                threshold=0.5, threshold_type="fixed", min_word_threshold=3
            )
        ),
    )

    ok = failed = 0
    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        for src in sources:
            url = src.get("url")
            brand = str(src.get("brand", "other")).lower()
            category = str(src.get("category", "other")).lower()
            if not url:
                print("skip: source with no url", file=sys.stderr)
                continue
            try:
                res = await crawler.arun(url=url, config=run_cfg)
            except Exception as exc:  # noqa: BLE001
                print(f"ERROR {url}: {exc}", file=sys.stderr)
                failed += 1
                continue
            if not res.success:
                print(f"FAIL  {url}: {res.error_message}", file=sys.stderr)
                failed += 1
                continue
            md = (
                getattr(res.markdown, "fit_markdown", "")
                or getattr(res.markdown, "raw_markdown", "")
                or (res.markdown if isinstance(res.markdown, str) else "")
            )
            md = clean_markdown(md)
            if len(md.strip()) < 200:
                print(f"THIN  {url}: {len(md.strip())} chars, skipped", file=sys.stderr)
                failed += 1
                continue
            out_dir = os.path.join(ROOT, BRAND_DIRS.get(brand, brand), category)
            os.makedirs(out_dir, exist_ok=True)
            out_path = os.path.join(out_dir, slugify(url) + ".md")
            with open(out_path, "w", encoding="utf-8") as fh:
                fh.write(frontmatter(src) + md.strip() + "\n")
            print(f"OK    {url} -> {os.path.relpath(out_path, ROOT)}")
            ok += 1

    print(f"\nDone: {ok} ok, {failed} failed, {len(sources)} total.")
    return 0  # never fail the job on individual-source errors


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
