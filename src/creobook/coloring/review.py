"""HTML contact sheet for a quick look before printing."""

from __future__ import annotations

import html
from pathlib import Path


def write_review(path: Path, rows: list[dict[str, str]]) -> Path:
    cards: list[str] = []
    for row in rows:
        title = html.escape(row["title"])
        status = html.escape(row["status"])
        warnings = html.escape(row.get("warnings") or "")
        image = row.get("thumb") or ""
        picture = (
            f'<img src="{html.escape(image)}" alt="{title}">'
            if image
            else '<div class="missing">bez náhledu</div>'
        )
        cards.append(
            "<article>"
            f"<p class=\"num\">{html.escape(row['number'])}</p>"
            f"{picture}"
            f"<h2>{title}</h2>"
            f"<p>{status}</p>"
            f"<p class=\"warn\">{warnings}</p>"
            "</article>"
        )
    document = f"""<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="utf-8">
<title>Náhled omalovánek</title>
<style>
body {{ font-family: sans-serif; margin: 24px; background: #fff; color: #111; }}
main {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 16px; }}
article {{ border: 1px solid #ddd; padding: 8px; }}
img {{ width: 100%; height: auto; background: #fff; }}
h2 {{ font-size: 14px; margin: 8px 0 4px; }}
p {{ margin: 0; font-size: 12px; }}
.warn {{ color: #8a3b00; }}
.missing {{ height: 120px; background: #f4f4f4; }}
</style>
</head>
<body>
<main>
{"".join(cards)}
</main>
</body>
</html>
"""
    path.write_text(document, encoding="utf-8")
    return path
