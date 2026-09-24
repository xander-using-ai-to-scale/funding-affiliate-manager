"""Render sendable documents from markdown: a PDF to upload or sign, and a .docx to edit.

    python3 scripts/build_documents.py docs/proposal-and-agreement-7ff.md [more.md ...]

Each FILE.md becomes FILE.pdf (headless Chrome, US Letter) and FILE.docx (pandoc) beside it.
Bracketed blanks like [state] are highlighted in the PDF so they're easy to find and fill.
"""

from __future__ import annotations

import html
import re
import subprocess
import sys
import tempfile
from pathlib import Path

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
CSS = """
@page { size: Letter; margin: 0.8in 0.85in 0.9in;
        @bottom-center { content: counter(page) " of " counter(pages); font: 9pt -apple-system, "Helvetica Neue", Arial, sans-serif; color: #6b7a75; } }
* { box-sizing: border-box; }
body { font: 10.5pt/1.5 -apple-system, "Helvetica Neue", Arial, sans-serif; color: #0e1a16; margin: 0; }
header { border-bottom: 2px solid #0f6b4f; padding-bottom: 14px; margin-bottom: 18px; }
header .title { font-size: 22pt; font-weight: 700; letter-spacing: -0.01em; margin: 0; line-height: 1.15; }
header .subtitle { font-size: 12pt; color: #4a5a55; margin: 4px 0 0; }
h1 { font-size: 15pt; color: #0f6b4f; margin: 22px 0 8px; padding-bottom: 4px; border-bottom: 1px solid #d6dfdb; }
section.level1 > h1 { margin-top: 0; }
h2 { font-size: 11.5pt; margin: 16px 0 5px; break-after: avoid; }
p { margin: 0 0 8px; }
ul { margin: 0 0 8px; padding-left: 20px; }
li { margin: 2px 0; }
table { border-collapse: collapse; width: 100%; margin: 6px 0 12px; break-inside: avoid; }
th, td { border: 1px solid #c9d4cf; padding: 5px 9px; text-align: left; vertical-align: top; }
th { background: #eef2f0; font-weight: 600; }
section.level2 { break-inside: avoid; }
.fill { background: #fff4d6; border-bottom: 1px dashed #c9a94a; padding: 0 2px; }
[data-sign] table { margin-top: 10px; }
[data-sign] td { height: 34px; width: 50%; }
"""


def render(md: Path) -> tuple[Path, Path]:
    meta = dict(re.findall(r"^(title|subtitle):\s*(.+)$", md.read_text().split("---", 2)[1], re.M))
    body = subprocess.run(["pandoc", str(md), "-f", "markdown", "-t", "html5", "--section-divs"], check=True,
                          capture_output=True, text=True).stdout
    body = re.sub(r"\[([^\[\]<>]{1,80})\]", r'<span class="fill">[\1]</span>', body)
    parts = [m.start() for m in re.finditer(r'<section id="[^"]*" class="level1"', body)]
    for pos in reversed(parts[1:]):  # each part after the first starts on a new page
        body = body[:pos] + '<section style="break-before:page"' + body[pos + len("<section"):]
    body = re.sub(r'(<section id="signatures" class="level2")', r'\1 data-sign', body, flags=re.S)
    page = (f'<!doctype html><html><head><meta charset="utf-8"><title>{html.escape(meta.get("title", md.stem))}</title>'
            f"<style>{CSS}</style></head><body><header><p class=\"title\">{html.escape(meta.get('title', ''))}</p>"
            f"<p class=\"subtitle\">{html.escape(meta.get('subtitle', ''))}</p></header>{body}</body></html>")
    pdf, docx = md.with_suffix(".pdf"), md.with_suffix(".docx")
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "doc.html"
        src.write_text(page)
        subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={pdf}", src.as_uri()], check=True, capture_output=True)
    subprocess.run(["pandoc", str(md), "-o", str(docx)], check=True)
    return pdf, docx


def main() -> None:
    for arg in sys.argv[1:] or ["docs/proposal-and-agreement-7ff.md"]:
        pdf, docx = render(Path(arg).resolve())
        print(f"{pdf}  ({pdf.stat().st_size:,} bytes)\n{docx}  ({docx.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
