"""HTML contact sheet before printing."""

from __future__ import annotations

import html
from pathlib import Path


def write_review(path: Path, rows: list[dict[str, str]]) -> Path:
    cards: list[str] = []
    for row in rows:
        title = html.escape(row["title"])
        warnings = html.escape(row.get("warnings") or "")
        picture = _image(row.get("thumb") or "", title)
        solution = _image(row.get("solution") or "", f"řešení {title}")
        cards.append(
            "<article>"
            f"<p class=\"num\">č. {html.escape(row['number'])}</p>"
            f"{picture}"
            f"<h2>{title}</h2>"
            f"<p>{html.escape(row.get('status') or '')}</p>"
            f"<p class=\"pos\">{html.escape(row.get('coordinates') or '')}</p>"
            f"<p class=\"warn\">{warnings}</p>"
            f"{solution}"
            "</article>"
        )
    document = f"""<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="utf-8">
<title>Náhled – Najdi slona!</title>
<style>
body {{ font-family: sans-serif; margin: 24px; background: #fff; color: #111; }}
main {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 16px; }}
article {{ border: 1px solid #ddd; padding: 8px; }}
img {{ width: 100%; height: auto; background: #fff; }}
h2 {{ font-size: 14px; margin: 8px 0 4px; }}
p {{ margin: 0 0 4px; font-size: 12px; }}
.warn {{ color: #8a3b00; }}
.pos {{ color: #333; }}
.missing {{ height: 80px; background: #f4f4f4; }}
</style>
</head>
<body>
<p>Automatická kontrola nepozná, jestli scéna neobsahuje dalšího slona. Prohlédni stránky ručně.</p>
<main>
{"".join(cards)}
</main>
</body>
</html>
"""
    path.write_text(document, encoding="utf-8")
    return path


def _image(relative: str, title: str) -> str:
    if not relative:
        return '<div class="missing">bez náhledu</div>'
    return f'<img src="{html.escape(relative)}" alt="{html.escape(title)}">'
