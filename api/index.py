"""Vercel entrypoint for the public demo.

Demo mode is hardcoded here, not read from configuration. This app is reachable
by anyone, and `demo=True` is what makes it impossible for a visitor to reach a
model and spend the owner's API budget: no client is constructed, and the
classification code is never called.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# The serverless runtime imports this file directly, and the project root is
# not reliably on sys.path when it does. Without this, `rfp_assistant` fails to
# import at deploy time rather than here.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rfp_assistant.web.app import create_app  # noqa: E402

app = create_app(
    demo=True,
    mode="replay",
    sample_path=ROOT / "fixtures" / "rfp-alderwood-retail.xlsx",
    demo_run_path=ROOT / "fixtures" / "demo-run.json",
)
