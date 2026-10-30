#!/usr/bin/env python3
"""Vygeneruje nové vydání sudoku, osmisměrek a bludišť a nahraje je do e-shopu.

Najde v kategorii Herní nejvyšší číslo každého sešitku, vygeneruje PDF
s dnešním seedem (YYYYMMDD) a založí nový produkt se stejným popisem,
krátkým popisem, obrázkem a kategoriemi jako dosavadní nejvyšší vydání.

Přihlášení je heslo aplikace WordPress (Uživatelé → Profil → Hesla aplikací):

    export WP_URL=https://www.creobook.cz
    export WP_USER=vas-ucet
    export WP_APP_PASSWORD='xxxx xxxx xxxx xxxx'
    uv run python scripts/publish_herni.py

Bez nahrání, jen s vygenerovanými PDF:

    uv run python scripts/publish_herni.py --dry-run

Jen zjistit další čísla, bez generování:

    uv run python scripts/publish_herni.py --dry-run --no-generate
"""

from __future__ import annotations

import argparse
import base64
import json
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

HERNI_CATEGORY_ID = 23
TITLE_NUMBER = re.compile(r" č\. (\d+)\s*$")
SLUG_NUMBER = re.compile(r"-(\d+)$")

# Meta, která patří ke starému PDF nebo k ceně. Nový soubor se nastaví zvlášť.
SKIP_META = {
    "_downloadable_files",
    "_price",
    "_regular_price",
    "_sale_price",
    "_thumbnail_id",
    "_product_image_gallery",
    "_edit_lock",
    "_edit_last",
}


@dataclass(frozen=True)
class Series:
    key: str
    title: str
    slug_prefix: str
    generate: Callable[[int, Path], Path]


@dataclass(frozen=True)
class Edition:
    series: Series
    number: int
    source_id: int
    source_name: str


def today_seed(today: date | None = None) -> int:
    day = today or date.today()
    return int(day.strftime("%Y%m%d"))


def edition_number(name: str, slug: str, title: str, slug_prefix: str) -> int | None:
    """Číslo vydání z názvu „Sudoku č. 2“, případně ze slugu ``sudoku-c-2``."""
    if name.startswith(title):
        match = TITLE_NUMBER.search(name.strip())
        if match:
            return int(match.group(1))
    if slug.startswith(slug_prefix):
        match = SLUG_NUMBER.search(slug)
        if match:
            return int(match.group(1))
    return None


def next_edition(products: list[dict[str, Any]], series: Series) -> Edition:
    found: list[tuple[int, dict[str, Any]]] = []
    for product in products:
        number = edition_number(
            str(product.get("name") or ""),
            str(product.get("slug") or ""),
            series.title,
            series.slug_prefix,
        )
        if number is not None:
            found.append((number, product))
    if not found:
        raise SystemExit(
            f"V kategorii Herní není žádný produkt „{series.title} č. N“. "
            "Skript nemá z čeho zkopírovat popis a obrázek."
        )
    number, source = max(found, key=lambda item: item[0])
    return Edition(
        series=series,
        number=number + 1,
        source_id=int(source["id"]),
        source_name=str(source.get("name") or ""),
    )


class Shop:
    def __init__(self, base_url: str, user: str | None = None, password: str | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.user = user
        self.password = password.replace(" ", "") if password else None

    def require_auth(self) -> None:
        if not self.user or not self.password:
            raise SystemExit(
                "Chybí WP_USER a WP_APP_PASSWORD. "
                "Heslo aplikace se vytváří ve WordPressu v profilu uživatele."
            )

    def _auth_header(self) -> dict[str, str]:
        self.require_auth()
        assert self.user is not None and self.password is not None
        token = base64.b64encode(f"{self.user}:{self.password}".encode()).decode("ascii")
        return {"Authorization": f"Basic {token}"}

    def request(
        self,
        method: str,
        path: str,
        *,
        query: dict[str, Any] | None = None,
        body: bytes | None = None,
        headers: dict[str, str] | None = None,
        auth: bool = False,
        timeout: int = 120,
    ) -> tuple[Any, dict[str, str]]:
        url = self.base_url + path
        if query:
            url += "?" + urlencode({k: v for k, v in query.items() if v is not None})
        req_headers = dict(headers or {})
        if auth:
            req_headers.update(self._auth_header())
        request = Request(url, data=body, headers=req_headers, method=method)
        try:
            with urlopen(request, timeout=timeout) as response:
                raw = response.read()
                header_map = {key.lower(): value for key, value in response.headers.items()}
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:2000]
            raise SystemExit(f"{method} {url} selhalo ({exc.code}): {detail}") from exc
        if not raw:
            return None, header_map
        return json.loads(raw.decode("utf-8")), header_map

    def list_herni_products(self, *, authenticated: bool) -> list[dict[str, Any]]:
        products: list[dict[str, Any]] = []
        page = 1
        while True:
            if authenticated:
                batch, headers = self.request(
                    "GET",
                    "/wp-json/wc/v3/products",
                    query={
                        "category": HERNI_CATEGORY_ID,
                        "per_page": 100,
                        "page": page,
                        "status": "any",
                    },
                    auth=True,
                )
            else:
                batch, headers = self.request(
                    "GET",
                    "/wp-json/wc/store/v1/products",
                    query={"category": HERNI_CATEGORY_ID, "per_page": 100, "page": page},
                )
            if not isinstance(batch, list) or not batch:
                break
            products.extend(batch)
            total_pages = int(headers.get("x-wp-totalpages", "1") or "1")
            if page >= total_pages or len(batch) < 100:
                break
            page += 1
        return products

    def get_product(self, product_id: int) -> dict[str, Any]:
        product, _headers = self.request(
            "GET",
            f"/wp-json/wc/v3/products/{product_id}",
            auth=True,
        )
        if not isinstance(product, dict):
            raise SystemExit(f"Produkt {product_id} se nepodařilo načíst.")
        return product

    def upload_pdf(self, pdf: Path, filename: str) -> str:
        payload = pdf.read_bytes()
        media, _headers = self.request(
            "POST",
            "/wp-json/wp/v2/media",
            body=payload,
            headers={
                "Content-Type": "application/pdf",
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
            auth=True,
            timeout=180,
        )
        if not isinstance(media, dict) or not media.get("source_url"):
            raise SystemExit(f"Nahrání {filename} nevrátilo adresu souboru.")
        return str(media["source_url"])

    def create_product(self, data: dict[str, Any]) -> dict[str, Any]:
        created, _headers = self.request(
            "POST",
            "/wp-json/wc/v3/products",
            body=json.dumps(data).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            auth=True,
        )
        if not isinstance(created, dict):
            raise SystemExit("Vytvoření produktu nevrátilo záznam.")
        return created


def product_payload(source: dict[str, Any], edition: Edition, file_url: str) -> dict[str, Any]:
    name = f"{edition.series.title} č. {edition.number}"
    images = [{"id": image["id"]} for image in source.get("images") or [] if image.get("id")]
    categories = [{"id": cat["id"]} for cat in source.get("categories") or [] if cat.get("id")]
    if not images:
        raise SystemExit(f"Produkt „{edition.source_name}“ nemá obrázek ke zkopírování.")
    if not categories:
        raise SystemExit(f"Produkt „{edition.source_name}“ nemá kategorie ke zkopírování.")
    meta = []
    for item in source.get("meta_data") or []:
        key = str(item.get("key") or "")
        if not key or key in SKIP_META:
            continue
        if "somdn" in key.lower() or "download" in key.lower():
            meta.append({"key": key, "value": item.get("value")})
    price = str(source.get("regular_price") or "0")
    payload: dict[str, Any] = {
        "name": name,
        "slug": f"{edition.series.slug_prefix}-{edition.number}",
        "type": source.get("type") or "simple",
        "status": "publish",
        "catalog_visibility": source.get("catalog_visibility") or "visible",
        "description": source.get("description") or "",
        "short_description": source.get("short_description") or "",
        "regular_price": price,
        "virtual": True,
        "downloadable": True,
        "downloads": [{"name": f"{name}.pdf", "file": file_url}],
        "download_limit": source.get("download_limit", -1),
        "download_expiry": source.get("download_expiry", -1),
        "categories": categories,
        "images": images,
        "manage_stock": False,
        "stock_status": "instock",
        "sold_individually": bool(source.get("sold_individually", False)),
    }
    if meta:
        payload["meta_data"] = meta
    return payload


def generate_sudoku(seed: int, output: Path) -> Path:
    from creobook.games.booklet import compile_games_booklet
    from creobook.games.models import BookletBuildOptions

    pages = output.with_name(output.stem + "-pages.pdf")
    result = compile_games_booklet(
        BookletBuildOptions(pack_id="sudoku", sheets=6, seed=seed, answers=True),
        pages,
        impose=True,
        booklet_output=output,
    )
    return result["booklet"]


def generate_word_search(seed: int, output: Path) -> Path:
    from creobook.games.word_search_booklet import compile_word_search_booklet

    result = compile_word_search_booklet(
        seed=seed,
        language="cs",
        easy=6,
        medium=6,
        hard=6,
        solutions=True,
        output=output,
    )
    return result["booklet"]


def generate_maze(seed: int, output: Path) -> Path:
    from creobook.games.maze_booklet import compile_maze_booklet

    result = compile_maze_booklet(
        seed=seed,
        easy=6,
        medium=6,
        hard=6,
        solutions=True,
        output=output,
    )
    return result["booklet"]


SERIES = (
    Series("sudoku", "Sudoku", "sudoku-c", generate_sudoku),
    Series("osmismerky", "Osmisměrky", "osmismerky-c", generate_word_search),
    Series("bludiste", "Bludiště", "bludiste-c", generate_maze),
)


def credentials_from_env() -> tuple[str, str | None, str | None]:
    import os

    return (
        os.environ.get("WP_URL", "https://www.creobook.cz"),
        os.environ.get("WP_USER") or None,
        os.environ.get("WP_APP_PASSWORD") or None,
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Seed vydání, výchozí je dnešní datum YYYYMMDD",
    )
    parser.add_argument(
        "--only",
        default="",
        help="Čárkou oddělený výběr: sudoku,osmismerky,bludiste",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="PDF vygeneruje, na web je nenahraje",
    )
    parser.add_argument(
        "--no-generate",
        action="store_true",
        help="Přeskočí generování PDF",
    )
    return parser.parse_args(argv)


def selected_series(only: str) -> tuple[Series, ...]:
    if not only.strip():
        return SERIES
    wanted = {part.strip() for part in only.split(",") if part.strip()}
    known = {series.key for series in SERIES}
    unknown = wanted - known
    if unknown:
        raise SystemExit(f"Neznámý sešitek: {', '.join(sorted(unknown))}. Povolené: {', '.join(sorted(known))}")
    return tuple(series for series in SERIES if series.key in wanted)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    seed = args.seed if args.seed is not None else today_seed()
    series_list = selected_series(args.only)
    base_url, user, password = credentials_from_env()
    shop = Shop(base_url, user, password)
    authenticated = bool(user and password) and not args.dry_run
    if not args.dry_run and not authenticated:
        shop.require_auth()

    products = shop.list_herni_products(authenticated=authenticated)
    editions = [next_edition(products, series) for series in series_list]
    booklet_dir = ROOT / "output" / "booklet"
    booklet_dir.mkdir(parents=True, exist_ok=True)

    for edition in editions:
        name = f"{edition.series.title} č. {edition.number}"
        pdf = booklet_dir / f"creobook-{seed}-{edition.series.slug_prefix}.pdf"
        print(f"{edition.source_name} → {name} (seed {seed})")
        if not args.no_generate:
            print(f"  generuji {pdf.name}")
            edition.series.generate(seed, pdf)
            print(f"  PDF: {pdf}")
        if args.dry_run:
            print("  nahrání přeskočeno (--dry-run)")
            continue
        if not pdf.is_file():
            raise SystemExit(f"Chybí PDF {pdf}. Spusťte skript bez --no-generate.")
        source = shop.get_product(edition.source_id)
        file_url = shop.upload_pdf(pdf, f"{edition.series.slug_prefix}-{edition.number}.pdf")
        created = shop.create_product(product_payload(source, edition, file_url))
        print(f"  produkt: {created.get('permalink')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
