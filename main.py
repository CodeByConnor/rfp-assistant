"""Deployment entrypoint for the public demo.

Vercel detects FastAPI from requirements.txt and loads a top-level `app` from
one of a fixed set of filenames at the project root (app.py, index.py,
server.py, main.py, wsgi.py, asgi.py) or inside src/ or app/. This file is that
entrypoint; it is named main.py rather than app.py only to avoid confusion with
rfp_assistant/web/app.py, which is the application itself.

Demo mode is hardcoded here rather than read from configuration. This app is
reachable by anyone, and `demo=True` is what makes it impossible for a visitor
to reach a model and spend the owner's API budget: no model client is
constructed, the classification code is never called, and the stateful routes
are never registered.

Run it the same way locally:

    python -m rfp_assistant serve --demo
"""

from pathlib import Path

from rfp_assistant.web.app import create_app

ROOT = Path(__file__).resolve().parent

app = create_app(
    demo=True,
    mode="replay",
    sample_path=ROOT / "fixtures" / "rfp-alderwood-retail.xlsx",
    demo_run_path=ROOT / "fixtures" / "demo-run.json",
)
