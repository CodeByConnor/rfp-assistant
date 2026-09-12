"""Vercel entrypoint for the public demo.

Demo mode is hardcoded here, not read from configuration. This app is reachable
by anyone, and `demo=True` is what makes it impossible for a visitor to reach a
model and spend the owner's API budget: no client is constructed, and the
classification code is never called.
"""

from pathlib import Path

from rfp_assistant.web.app import create_app

ROOT = Path(__file__).resolve().parent.parent

app = create_app(
    demo=True,
    mode="replay",
    sample_path=ROOT / "fixtures" / "rfp-alderwood-retail.xlsx",
    demo_run_path=ROOT / "fixtures" / "demo-run.json",
)
