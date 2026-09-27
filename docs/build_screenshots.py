"""Regenerate the README screenshots from a running demo.

Committed so the images in the README can be reproduced rather than being
undocumented artefacts that drift from the UI. Playwright is not in any
requirements file, because it is only needed to regenerate images:

    pip install playwright && playwright install chromium
    python -m rfp_assistant serve --demo --port 8766 &
    python docs/build_screenshots.py

Light colour scheme on purpose: the images sit in a README that most people
read on a light background.
"""

from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8766"
OUT = Path(__file__).resolve().parent / "screenshots"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(
            viewport={"width": 1280, "height": 900},
            device_scale_factor=2,
            color_scheme="light",
        )

        page.goto(URL, wait_until="networkidle")
        page.evaluate("try { localStorage.clear(); } catch (e) {}")
        page.reload(wait_until="networkidle")

        page.click("#sampleBtn")
        page.wait_for_selector("#rows tr.row", timeout=60_000)
        # Outlast the "248 requirements extracted" toast, which otherwise sits
        # over the bottom-right of every shot.
        page.wait_for_timeout(4_500)
        page.screenshot(path=OUT / "review.png")
        print(f"wrote {OUT / 'review.png'}")

        # The guardrail holding an answer is the thing worth showing.
        page.evaluate("setFilter('escalated')")
        page.wait_for_timeout(300)
        page.evaluate(
            "const r = state.run.rows.find(x => x.overridden_from); toggle(r.rid)"
        )
        page.wait_for_timeout(500)
        page.locator(".table-wrap").screenshot(path=OUT / "guardrail.png")
        print(f"wrote {OUT / 'guardrail.png'}")

        # A blocking gap: a hard No against a requirement marked mandatory.
        page.evaluate("setFilter('blocking')")
        page.wait_for_timeout(400)
        page.locator(".table-wrap").screenshot(path=OUT / "blocking.png")
        print(f"wrote {OUT / 'blocking.png'}")

        browser.close()


if __name__ == "__main__":
    main()
