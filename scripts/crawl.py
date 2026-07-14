#!/usr/bin/env python3
"""Crawl the sources listed in ../sources.yaml into cleaned markdown.

Each source becomes  <brand>/<category>/<slug>.md  with YAML frontmatter.
Run via the "Crawl sources" GitHub Action (manual trigger).

Two things this script deliberately does NOT do:

1. It does not hammer hosts. gsmarena.com rate-limits at roughly one request per
   10-15s and escalates to a multi-hour IP ban on sustained bursts (observed:
   HTTP 429 with `Retry-After: 36000`). PER_HOST_DELAY throttles per hostname, so
   a long specs sweep stays under that. Without it, a large run gets the runner
   banned partway through and most sources fail.

2. It does not exit 0 no matter what. Individual source failures are still
   tolerated (a dead URL should not sink a 70-source run), but if the failure
   RATE crosses FAIL_THRESHOLD the run exits non-zero. Previously any outcome —
   including "banned on request 3, everything after failed" — reported success,
   and the commit step simply found nothing to commit and said "No changes."
   A crawl that silently fetched nothing must not look like a crawl that found
   nothing new.
"""
import asyncio
import os
import re
import sys
from datetime import datetime, timezone
from urllib.parse import urlparse

import yaml
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES_FILE = os.path.join(ROOT, "sources.yaml")

# Seconds to wait between two requests to the SAME host. gsmarena bans on bursts;
# the support sites are far more tolerant, so they get a smaller courtesy delay.
PER_HOST_DELAY = {"www.gsmarena.com": 20.0, "m.gsmarena.com": 20.0}
DEFAULT_HOST_DELAY = 2.0

# Fail the run if more than this fraction of sources failed. Catches the case
# that motivated it: getting rate-limit-banned mid-run, where nearly everything
# after the ban fails but the job would otherwise stay green.
FAIL_THRESHOLD = 0.30

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


# Bot-check / block interstitials. These come back with HTTP 200 and plenty of
# text, so neither the status code nor the length gate rejects them.
BLOCKED = re.compile(
    r"(Just a moment"
    r"|Enable JavaScript and cookies to continue"
    r"|Checking your browser"
    r"|Attention Required"
    r"|cf-turnstile|cf-browser-verification"
    r"|Access Denied"
    r"|Too Many Requests"
    r"|Verify you are human"
    r"|unusual traffic)",
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
        # mi.com's support FAQ pages render their body client-side. Returning as
        # soon as the DOM is ready captured an empty shell — 14 of them came back
        # at exactly 17 chars and were dropped as THIN, which reads like a bad URL
        # but was really us not waiting for the render. Wait for the network to go
        # quiet, then give the page a moment to paint.
        wait_until="networkidle",
        delay_before_return_html=2.5,
        page_timeout=45000,
        markdown_generator=DefaultMarkdownGenerator(
            content_filter=PruningContentFilter(
                threshold=0.5, threshold_type="fixed", min_word_threshold=3
            )
        ),
    )

    ok = failed = 0
    failures: list[str] = []
    last_hit: dict[str, float] = {}

    async def throttle(url: str) -> None:
        """Space out requests to the same host. gsmarena bans on bursts."""
        host = urlparse(url).netloc.lower()
        delay = PER_HOST_DELAY.get(host, DEFAULT_HOST_DELAY)
        loop = asyncio.get_running_loop()
        prev = last_hit.get(host)
        if prev is not None:
            wait = delay - (loop.time() - prev)
            if wait > 0:
                await asyncio.sleep(wait)
        last_hit[host] = loop.time()

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        for src in sources:
            url = src.get("url")
            brand = str(src.get("brand", "other")).lower()
            category = str(src.get("category", "other")).lower()
            if not url:
                print("skip: source with no url", file=sys.stderr)
                continue
            await throttle(url)
            try:
                res = await crawler.arun(url=url, config=run_cfg)
            except Exception as exc:  # noqa: BLE001
                print(f"ERROR {url}: {exc}", file=sys.stderr)
                failures.append(url)
                failed += 1
                continue
            if not res.success:
                print(f"FAIL  {url}: {res.error_message}", file=sys.stderr)
                failures.append(url)
                failed += 1
                continue
            md = (
                getattr(res.markdown, "fit_markdown", "")
                or getattr(res.markdown, "raw_markdown", "")
                or (res.markdown if isinstance(res.markdown, str) else "")
            )
            md = clean_markdown(md)
            # A bot-check interstitial is served with HTTP 200 and enough text to
            # clear the length gate, so status and size alone cannot catch it.
            # Without this it would be written into the corpus as if it were the
            # article — a silent poisoning that is far worse than a failed fetch.
            if BLOCKED.search(md[:1500]):
                print(f"BLOCKED {url}: bot-check/challenge page, not real content", file=sys.stderr)
                failures.append(url)
                failed += 1
                continue
            if len(md.strip()) < 200:
                print(f"THIN  {url}: {len(md.strip())} chars, skipped", file=sys.stderr)
                failures.append(url)
                failed += 1
                continue
            out_dir = os.path.join(ROOT, BRAND_DIRS.get(brand, brand), category)
            os.makedirs(out_dir, exist_ok=True)
            out_path = os.path.join(out_dir, slugify(url) + ".md")
            with open(out_path, "w", encoding="utf-8") as fh:
                fh.write(frontmatter(src) + md.strip() + "\n")
            print(f"OK    {url} -> {os.path.relpath(out_path, ROOT)}")
            ok += 1

    total = len(sources)
    print(f"\nDone: {ok} ok, {failed} failed, {total} total.")

    if failures:
        print("\nFailed sources:", file=sys.stderr)
        for u in failures:
            print(f"  - {u}", file=sys.stderr)

    # A dead URL or two should not sink a 70-source run, but a run where most
    # sources failed means something systemic (rate-limit ban, network, a site
    # redesign) — and that must NOT be reported as success. Before this guard the
    # script returned 0 unconditionally, so a fully-banned run finished green and
    # the commit step just reported "No changes to commit."
    if total and failed / total > FAIL_THRESHOLD:
        print(
            f"\nFATAL: {failed}/{total} sources failed "
            f"({failed / total:.0%} > {FAIL_THRESHOLD:.0%} threshold). "
            "This is a systemic failure, not a few dead links — check for a "
            "rate-limit ban before re-running.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
