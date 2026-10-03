"""The droplet renderer: browser-box and data-box are read-only and only present with a token.

    python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SETUP = (ROOT / "deploy" / "droplet" / "setup.sh").read_text()
RENDERER = re.search(r'config\.template\.yaml" "\$HERMES_HOME/config\.yaml" <<\'PY\'\n(.*?)\nPY\n', SETUP, re.S).group(1)
BASE_ENV = {
    "HERMES_PY": sys.executable, "PRIMARY_MODEL": "m", "REPO_DIR": "/r", "FAM_HOME": "/f",
    "VAULT_DIR": "/v", "GHL_CLI_DIR": "/g", "FAM_GHL_MODE": "demo",
}
BOX_KEYS = ("BROWSER_BOX_URL", "BROWSER_BOX_TOKEN", "DATABOX_URL", "DATABOX_TOKEN", "SUPER_BROWSER_TOKEN")


def render(extra: dict[str, str]) -> str:
    env = {k: v for k, v in os.environ.items() if k not in BOX_KEYS}
    env.update(BASE_ENV, **extra)
    with tempfile.TemporaryDirectory() as tmp:
        script, out = Path(tmp) / "render.py", Path(tmp) / "config.yaml"
        script.write_text(RENDERER)
        subprocess.run([sys.executable, str(script), str(ROOT / "hermes" / "config.template.yaml"), str(out)],
                       env=env, check=True)
        return out.read_text()


class BoxRenderTests(unittest.TestCase):
    def test_boxes_are_left_out_without_tokens(self):
        text = render({})
        self.assertNotIn("  browser-box:", text)
        self.assertNotIn("  data-box:", text)

    def test_boxes_are_read_only_and_accept_either_url_form(self):
        for url in ("https://box.example.test", "https://box.example.test/mcp/"):
            text = render({"BROWSER_BOX_URL": url, "BROWSER_BOX_TOKEN": "t",
                           "DATABOX_URL": url, "DATABOX_TOKEN": "t"})
            self.assertEqual(text.count("url: https://box.example.test/mcp\n"), 2, url)
            self.assertIn("include: [fetch, read, session, status]", text)
            # Priced pulls (plan/execute/sources) go through paid enrichment, which SOUL.md forbids.
            self.assertIn("include: [status, scrape, job]", text)


if __name__ == "__main__":
    unittest.main()
