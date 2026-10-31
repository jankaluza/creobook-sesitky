#!/usr/bin/env python3
"""Vygeneruje nové vydání sudoku, osmisměrek, bludišť a omalovánek a nahraje je do e-shopu.

Najde v kategorii Herní nejvyšší číslo každého sešitku a vygeneruje PDF
s dnešním seedem (YYYYMMDD). Náhled produktu je prostřední stránka sešitku.
Když už produkt se stejným seedem existuje, přepíše jeho PDF a náhled.
Jinak založí další číslo se stejným popisem, krátkým popisem a kategoriemi.

Omalovánky přidají jedno téma ze seznamu, které na e-shopu ještě není.
Popis, kategorie a cenu vezmou z produktu Omalovánky – Lesní kamarádi.
Stejný seed v tentýž den aktualizuje dnešní omalovánky místo dalšího tématu.
Generování obrázků je placené a chce OPENAI_API_KEY. Bez klíče se omalovánky
přeskočí a ostatní sešitky se nahrají dál.

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
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

HERNI_CATEGORY_ID = 23
SEED_META = "_creobook_seed"
COLORING_TEMPLATE_SLUG = "omalovanky-lesni-kamaradi"
COLORING_SKU_PREFIX = "omalovanky"
COLORING_ILLUSTRATIONS = 16
COLORING_THEME_TITLES = (
    "Lesní kamarádi",
    "Zvířátka na farmě",
    "Život pod hladinou moře",
    "Dinosauří svět",
    "Zvířata africké savany",
    "Domácí mazlíčci",
    "Kočky a koťátka",
    "Psi a štěňátka",
    "Koně a poníci",
    "Motýli a broučci",
    "Ptáci našich zahrad",
    "Zvířata v džungli",
    "Polární zvířata",
    "Zvířecí mláďátka",
    "Život u rybníka",
    "Včelky a jejich svět",
    "Zvířata v horách",
    "Noční zvířátka",
    "Život na louce",
    "Kouzelná zahrada",
    "Draci a dračí mláďata",
    "Princezny a království",
    "Rytíři a hrady",
    "Jednorožci",
    "Víly a skřítkové",
    "Čarodějové a kouzla",
    "Mořské panny",
    "Pohádkový les",
    "Kouzelná zvířátka",
    "Trpaslíci a jejich domečky",
    "Obři a malí hrdinové",
    "Piráti a poklady",
    "Kouzelné školy",
    "Létající ostrovy",
    "Podmořské království",
    "Tajemné jeskyně",
    "Pohádkové chaloupky",
    "Cesta za pokladem",
    "Malí superhrdinové",
    "Fantastická stvoření",
    "Vesmírná dobrodružství",
    "Astronauti na cizích planetách",
    "Rakety a kosmické lodě",
    "Roboti a robotí kamarádi",
    "Auta a závodní dráhy",
    "Stavební stroje",
    "Vlaky a železnice",
    "Letadla a letiště",
    "Lodě a přístavy",
    "Hasičská auta a hasiči",
    "Policejní dobrodružství",
    "Traktory a zemědělské stroje",
    "Motorky a čtyřkolky",
    "Stroje budoucnosti",
    "Vynálezy malých vědců",
    "Den ve škole",
    "Moje rodina",
    "Hry na hřišti",
    "Sportovní dobrodružství",
    "Malí kuchaři a cukráři",
    "Pečení dortů a sušenek",
    "Malí zahradníci",
    "Doktoři a veterináři",
    "Záchranáři v akci",
    "Život ve městě",
    "Vesnice a venkov",
    "Na výletě v přírodě",
    "Kempování pod hvězdami",
    "Cirkus a artisté",
    "Hudební nástroje a muzikanti",
    "Jarní probouzení přírody",
    "Velikonoční zajíčci",
    "Letní prázdniny",
    "Dobrodružství u moře",
    "Podzimní les",
    "Dýně a podzimní radovánky",
    "Zimní radovánky",
    "Sněhuláci a sněhové stavby",
    "Vánoční kouzlení",
    "Mikuláš, čerti a andělé",
    "Karnevalové masky",
    "Narozeninová oslava",
    "Halloween pro děti",
    "Silvestr a ohňostroje",
    "Čtyři roční období",
    "Bláznivá příšerky",
    "Domečky na stromech",
    "Zvířátka v oblečení",
    "Veselá jídla s obličeji",
    "Sladkosti a zmrzliny",
    "Ostrov plný dobrodružství",
    "Cesta kolem světa",
    "Slavné světové památky",
    "Tajemství starověkého Egypta",
    "Pravěcí lidé a mamuti",
    "Podmořští průzkumníci",
    "Zábavní park a kolotoče",
    "Bludiště a kouzelné cesty",
    "Malí detektivové",
    "Můj vysněný svět",
)
TITLE_NUMBER = re.compile(r" č\. (\d+)\s*$")
SLUG_NUMBER = re.compile(r"-(\d+)$")
PREVIEW_DPI = 144

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
    generate: Callable[[int, Path, str], Path]


@dataclass(frozen=True)
class Edition:
    series: Series
    number: int
    source_id: int
    source_name: str
    update_id: int | None = None

    @property
    def updates_existing(self) -> bool:
        return self.update_id is not None


@dataclass(frozen=True)
class ColoringTheme:
    title: str

    @property
    def slug(self) -> str:
        from creobook.coloring.workflow import slugify

        return f"{COLORING_SKU_PREFIX}-{slugify(self.title)}"

    @property
    def product_name(self) -> str:
        return f"Omalovánky – {self.title}"


COLORING_THEMES = tuple(ColoringTheme(title) for title in COLORING_THEME_TITLES)


@dataclass(frozen=True)
class ColoringEdition:
    theme: ColoringTheme
    source_id: int
    source_name: str
    update_id: int | None = None

    @property
    def updates_existing(self) -> bool:
        return self.update_id is not None


def booklet_number(number: int) -> str:
    """Zápis čísla v názvu produktu, například „č. 2“ v „Sudoku č. 2“."""
    return f"č. {number}"


def product_name(title: str, number: int) -> str:
    return f"{title} {booklet_number(number)}"


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


def seed_day(seed: int) -> str | None:
    """``20261030`` → ``2026-10-30``. Jiný seed datum není."""
    text = str(seed)
    if len(text) != 8 or not text.isdigit():
        return None
    try:
        parsed = date(int(text[:4]), int(text[4:6]), int(text[6:8]))
    except ValueError:
        return None
    return parsed.isoformat()


def edition_sku(series: Series, seed: int) -> str:
    return f"{series.slug_prefix}-{seed}"


def stored_seed(product: dict[str, Any], series: Series) -> int | None:
    """Seed uložený v meta nebo v SKU ``sudoku-c-20261030``."""
    for item in product.get("meta_data") or []:
        if str(item.get("key") or "") != SEED_META:
            continue
        value = str(item.get("value") or "")
        if value.isdigit():
            return int(value)
    sku = str(product.get("sku") or "")
    prefix = f"{series.slug_prefix}-"
    if sku.startswith(prefix):
        suffix = sku[len(prefix) :]
        if len(suffix) == 8 and suffix.isdigit():
            return int(suffix)
    return None


def created_on_seed_day(product: dict[str, Any], seed: int) -> bool:
    day = seed_day(seed)
    if day is None:
        return False
    for key in ("date_created", "date_created_gmt"):
        if str(product.get(key) or "").startswith(day):
            return True
    return False


def series_products(
    products: list[dict[str, Any]], series: Series
) -> list[tuple[int, dict[str, Any]]]:
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
    return found


def plan_edition(products: list[dict[str, Any]], series: Series, seed: int) -> Edition:
    """Další číslo, nebo aktualizace posledního produktu se stejným seedem."""
    found = series_products(products, series)
    if not found:
        raise SystemExit(
            f"V kategorii Herní není žádný produkt „{series.title} č. N“. "
            "Skript nemá z čeho zkopírovat popis."
        )
    same_seed = [item for item in found if stored_seed(item[1], series) == seed]
    if same_seed:
        number, product = max(same_seed, key=lambda item: item[0])
        return _edition_update(series, number, product)
    number, latest = max(found, key=lambda item: item[0])
    if stored_seed(latest, series) is None and created_on_seed_day(latest, seed):
        return _edition_update(series, number, latest)
    return Edition(
        series=series,
        number=number + 1,
        source_id=int(latest["id"]),
        source_name=str(latest.get("name") or ""),
    )


def _edition_update(series: Series, number: int, product: dict[str, Any]) -> Edition:
    return Edition(
        series=series,
        number=number,
        source_id=int(product["id"]),
        source_name=str(product.get("name") or ""),
        update_id=int(product["id"]),
    )


def _folded_name(name: str) -> str:
    text = name.strip().casefold().replace("–", "-").replace("—", "-")
    text = re.sub(r"\s*-\s*", "-", text)
    return re.sub(r"\s+", " ", text)


def theme_of_product(product: dict[str, Any]) -> ColoringTheme | None:
    slug = str(product.get("slug") or "")
    name = _folded_name(str(product.get("name") or ""))
    for theme in COLORING_THEMES:
        if slug == theme.slug or name == _folded_name(theme.product_name):
            return theme
    return None


def _coloring_template(products: list[dict[str, Any]]) -> dict[str, Any] | None:
    for product in products:
        if str(product.get("slug") or "") == COLORING_TEMPLATE_SLUG:
            return product
    first = COLORING_THEMES[0]
    for product in products:
        if theme_of_product(product) == first:
            return product
    return None


def plan_coloring(products: list[dict[str, Any]], seed: int) -> ColoringEdition | None:
    """Další chybějící téma, nebo aktualizace omalovánek se stejným seedem."""
    template = _coloring_template(products)
    if template is None:
        raise SystemExit(
            "Na e-shopu chybí vzor „Omalovánky – Lesní kamarádi“ "
            f"(slug {COLORING_TEMPLATE_SLUG}). Skript nemá z čeho zkopírovat popis."
        )
    prefix = SimpleNamespace(slug_prefix=COLORING_SKU_PREFIX)
    same_seed = [
        product
        for product in products
        if theme_of_product(product) is not None and stored_seed(product, prefix) == seed
    ]
    if same_seed:
        product = max(same_seed, key=lambda item: int(item["id"]))
        theme = theme_of_product(product)
        assert theme is not None
        return ColoringEdition(
            theme=theme,
            source_id=int(template["id"]),
            source_name=str(template.get("name") or ""),
            update_id=int(product["id"]),
        )
    taken = {theme_of_product(product) for product in products}
    for theme in COLORING_THEMES:
        if theme not in taken:
            return ColoringEdition(
                theme=theme,
                source_id=int(template["id"]),
                source_name=str(template.get("name") or ""),
            )
    return None


def coloring_output_dir(theme: ColoringTheme) -> Path:
    from creobook.coloring.workflow import slugify

    return ROOT / "output" / "coloring" / slugify(theme.title)


def merge_products(*groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen: set[Any] = set()
    for group in groups:
        for product in group:
            identity = product.get("id")
            if identity in seen:
                continue
            seen.add(identity)
            merged.append(product)
    return merged


def middle_page_number(page_count: int) -> int:
    """1-based prostřední stránka. U sudého počtu ta bližší k začátku."""
    if page_count < 1:
        raise ValueError("PDF nemá žádnou stránku")
    return (page_count + 1) // 2


def pages_pdf_for(booklet: Path) -> Path:
    return booklet.with_name(booklet.stem + "-pages.pdf")


def render_middle_page(pdf: Path, output: Path, *, dpi: int = PREVIEW_DPI) -> int:
    """PNG prostřední stránky sešitku v pořadí čtení."""
    from pypdf import PdfReader

    if shutil.which("pdftoppm") is None:
        raise SystemExit("Chybí pdftoppm. Na serveru ho dodá balíček poppler-utils.")
    page_count = len(PdfReader(str(pdf)).pages)
    page = middle_page_number(page_count)
    output.parent.mkdir(parents=True, exist_ok=True)
    prefix = output.with_suffix("")
    try:
        subprocess.run(
            [
                "pdftoppm",
                "-png",
                "-r",
                str(dpi),
                "-f",
                str(page),
                "-l",
                str(page),
                "-singlefile",
                str(pdf),
                str(prefix),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "").strip()
        raise SystemExit(f"Náhled stránky {page} se nepodařilo vykreslit: {detail}") from exc
    if not output.is_file():
        raise SystemExit(f"pdftoppm nevytvořil {output.name}.")
    return page


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

    def list_products(self, *, authenticated: bool, query: dict[str, Any]) -> list[dict[str, Any]]:
        products: list[dict[str, Any]] = []
        page = 1
        while True:
            page_query = dict(query)
            page_query["per_page"] = 100
            page_query["page"] = page
            if authenticated:
                page_query["status"] = "any"
                batch, headers = self.request(
                    "GET",
                    "/wp-json/wc/v3/products",
                    query=page_query,
                    auth=True,
                )
            else:
                batch, headers = self.request(
                    "GET",
                    "/wp-json/wc/store/v1/products",
                    query=page_query,
                )
            if not isinstance(batch, list) or not batch:
                break
            products.extend(batch)
            total_pages = int(headers.get("x-wp-totalpages", "1") or "1")
            if page >= total_pages or len(batch) < 100:
                break
            page += 1
        return products

    def list_herni_products(self, *, authenticated: bool) -> list[dict[str, Any]]:
        return self.list_products(authenticated=authenticated, query={"category": HERNI_CATEGORY_ID})

    def list_omalovanky(self, *, authenticated: bool) -> list[dict[str, Any]]:
        return self.list_products(authenticated=authenticated, query={"search": "Omalovánky"})

    def get_product(self, product_id: int) -> dict[str, Any]:
        product, _headers = self.request(
            "GET",
            f"/wp-json/wc/v3/products/{product_id}",
            auth=True,
        )
        if not isinstance(product, dict):
            raise SystemExit(f"Produkt {product_id} se nepodařilo načíst.")
        return product

    def upload_media(self, path: Path, filename: str, content_type: str) -> dict[str, Any]:
        media, _headers = self.request(
            "POST",
            "/wp-json/wp/v2/media",
            body=path.read_bytes(),
            headers={
                "Content-Type": content_type,
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
            auth=True,
            timeout=180,
        )
        if not isinstance(media, dict) or not media.get("id") or not media.get("source_url"):
            raise SystemExit(f"Nahrání {filename} nevrátilo soubor v knihovně médií.")
        return media

    def upload_pdf(self, pdf: Path, filename: str) -> str:
        return str(self.upload_media(pdf, filename, "application/pdf")["source_url"])

    def upload_png(self, png: Path, filename: str) -> int:
        return int(self.upload_media(png, filename, "image/png")["id"])

    def save_product(self, data: dict[str, Any], product_id: int | None = None) -> dict[str, Any]:
        path = "/wp-json/wc/v3/products"
        if product_id is not None:
            path += f"/{product_id}"
        saved, _headers = self.request(
            "PUT" if product_id is not None else "POST",
            path,
            body=json.dumps(data).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            auth=True,
        )
        if not isinstance(saved, dict):
            action = "Aktualizace" if product_id is not None else "Vytvoření"
            raise SystemExit(f"{action} produktu nevrátila záznam.")
        return saved


def seed_meta_entry(source: dict[str, Any], seed: int) -> dict[str, Any]:
    entry: dict[str, Any] = {"key": SEED_META, "value": str(seed)}
    for item in source.get("meta_data") or []:
        if str(item.get("key") or "") == SEED_META and item.get("id"):
            entry["id"] = item["id"]
            break
    return entry


def product_payload(
    source: dict[str, Any],
    edition: Edition,
    file_url: str,
    image_id: int,
    seed: int,
) -> dict[str, Any]:
    name = product_name(edition.series.title, edition.number)
    return catalog_payload(
        source,
        name=name,
        slug=f"{edition.series.slug_prefix}-{edition.number}",
        sku=edition_sku(edition.series, seed),
        file_url=file_url,
        image_id=image_id,
        seed=seed,
    )


def coloring_payload(
    source: dict[str, Any],
    edition: ColoringEdition,
    file_url: str,
    image_id: int,
    seed: int,
) -> dict[str, Any]:
    return catalog_payload(
        source,
        name=edition.theme.product_name,
        slug=edition.theme.slug,
        sku=f"{COLORING_SKU_PREFIX}-{seed}",
        file_url=file_url,
        image_id=image_id,
        seed=seed,
    )


def catalog_payload(
    source: dict[str, Any],
    *,
    name: str,
    slug: str,
    sku: str,
    file_url: str,
    image_id: int,
    seed: int,
) -> dict[str, Any]:
    categories = [{"id": cat["id"]} for cat in source.get("categories") or [] if cat.get("id")]
    if not categories:
        raise SystemExit("Vzor produktu nemá kategorie ke zkopírování.")
    meta = []
    for item in source.get("meta_data") or []:
        key = str(item.get("key") or "")
        if not key or key in SKIP_META or key == SEED_META:
            continue
        if "somdn" in key.lower() or "download" in key.lower():
            copied = {"key": key, "value": item.get("value")}
            if item.get("id"):
                copied["id"] = item["id"]
            meta.append(copied)
    meta.append(seed_meta_entry(source, seed))
    price = str(source.get("regular_price") or "0")
    return {
        "name": name,
        "slug": slug,
        "sku": sku,
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
        "images": [{"id": image_id}],
        "manage_stock": False,
        "stock_status": "instock",
        "sold_individually": bool(source.get("sold_individually", False)),
        "meta_data": meta,
    }


def generate_sudoku(seed: int, output: Path, edition_label: str) -> Path:
    from creobook.games.booklet import compile_games_booklet
    from creobook.games.models import BookletBuildOptions

    pages = output.with_name(output.stem + "-pages.pdf")
    result = compile_games_booklet(
        BookletBuildOptions(
            pack_id="sudoku",
            sheets=6,
            seed=seed,
            answers=True,
            edition_label=edition_label,
        ),
        pages,
        impose=True,
        booklet_output=output,
    )
    return result["booklet"]


def generate_word_search(seed: int, output: Path, edition_label: str) -> Path:
    from creobook.games.word_search_booklet import compile_word_search_booklet

    result = compile_word_search_booklet(
        seed=seed,
        language="cs",
        easy=6,
        medium=6,
        hard=6,
        solutions=True,
        output=output,
        edition_label=edition_label,
    )
    return result["booklet"]


def generate_maze(seed: int, output: Path, edition_label: str) -> Path:
    from creobook.games.maze_booklet import compile_maze_booklet

    result = compile_maze_booklet(
        seed=seed,
        easy=6,
        medium=6,
        hard=6,
        solutions=True,
        output=output,
        edition_label=edition_label,
    )
    return result["booklet"]


def generate_coloring(theme: ColoringTheme) -> tuple[Path, Path]:
    from creobook.coloring.booklet import filled_illustration_count
    from creobook.coloring.models import ColoringConfig, ColoringError
    from creobook.coloring.workflow import run_coloring_book

    output_dir = coloring_output_dir(theme)
    filled = filled_illustration_count(COLORING_ILLUSTRATIONS)
    config = ColoringConfig(
        theme=theme.title,
        title=theme.title,
        age_group="6-8",
        illustration_count=COLORING_ILLUSTRATIONS,
        page_format="A5",
        output_directory=str(output_dir),
        max_new=filled,
    )
    try:
        report = run_coloring_book(config, generate=True)
    except ColoringError as exc:
        raise SystemExit(str(exc)) from exc
    for note in report.notes:
        print(f"  {note}")
    if report.print_pdf is None or report.reading_pdf is None:
        raise SystemExit(
            "Omalovánky nemají obě PDF. Podívejte se na review.html v adresáři sešitku."
        )
    return report.print_pdf, report.reading_pdf


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
        help="Čárkou oddělený výběr: sudoku,osmismerky,bludiste,omalovanky",
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


def selected_jobs(only: str) -> tuple[tuple[Series, ...], bool]:
    known = {series.key for series in SERIES} | {"omalovanky"}
    if not only.strip():
        return SERIES, True
    wanted = {part.strip() for part in only.split(",") if part.strip()}
    unknown = wanted - known
    if unknown:
        raise SystemExit(
            f"Neznámý sešitek: {', '.join(sorted(unknown))}. Povolené: {', '.join(sorted(known))}"
        )
    return tuple(series for series in SERIES if series.key in wanted), "omalovanky" in wanted


def openai_key_present() -> bool:
    import os

    return bool(os.environ.get("OPENAI_API_KEY", "").strip())


def publish_coloring(
    shop: Shop,
    edition: ColoringEdition,
    seed: int,
    *,
    dry_run: bool,
    no_generate: bool,
) -> None:
    action = "aktualizuji" if edition.updates_existing else "nový produkt"
    print(f"{edition.source_name} → {edition.theme.product_name} (seed {seed}, {action})")
    output_dir = coloring_output_dir(edition.theme)
    folder = output_dir.name
    print_pdf = output_dir / f"{folder}-tisk.pdf"
    reading_pdf = output_dir / f"{folder}-a5.pdf"
    preview = ROOT / "output" / "preview" / f"{edition.theme.slug}.png"
    if dry_run:
        print("  generování přeskočeno (--dry-run, obrázky jsou placené)")
        return
    if not no_generate:
        print(f"  generuji {edition.theme.product_name}")
        print_pdf, reading_pdf = generate_coloring(edition.theme)
    if not print_pdf.is_file() or not reading_pdf.is_file():
        raise SystemExit(
            f"Chybí {print_pdf.name} nebo {reading_pdf.name}. Spusťte skript bez --no-generate."
        )
    page = render_middle_page(reading_pdf, preview)
    print(f"  náhled: {preview.name}, stránka {page}")
    source = shop.get_product(edition.source_id)
    file_url = shop.upload_pdf(print_pdf, f"{edition.theme.slug}.pdf")
    image_id = shop.upload_png(preview, f"{edition.theme.slug}.png")
    saved = shop.save_product(
        coloring_payload(source, edition, file_url, image_id, seed),
        edition.update_id,
    )
    print(f"  produkt: {saved.get('permalink')}")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    seed = args.seed if args.seed is not None else today_seed()
    series_list, include_coloring = selected_jobs(args.only)
    base_url, user, password = credentials_from_env()
    shop = Shop(base_url, user, password)
    can_auth = bool(user and password)
    if not args.dry_run and not can_auth:
        shop.require_auth()

    products = shop.list_herni_products(authenticated=can_auth)
    editions = [plan_edition(products, series, seed) for series in series_list]
    coloring_job = None
    if include_coloring:
        catalog = merge_products(products, shop.list_omalovanky(authenticated=can_auth))
        coloring_job = plan_coloring(catalog, seed)
        if coloring_job is None:
            print("Všechna témata omalovánek už na e-shopu jsou.")
        elif not args.dry_run and not args.no_generate and not openai_key_present():
            message = (
                "Omalovánky přeskočeny: chybí OPENAI_API_KEY. "
                "Doplňte ho do /etc/creobook/herni.env."
            )
            if not series_list:
                raise SystemExit(message)
            print(message)
            coloring_job = None
    booklet_dir = ROOT / "output" / "booklet"
    booklet_dir.mkdir(parents=True, exist_ok=True)
    preview_dir = ROOT / "output" / "preview"
    preview_dir.mkdir(parents=True, exist_ok=True)

    for edition in editions:
        name = product_name(edition.series.title, edition.number)
        label = booklet_number(edition.number)
        pdf = booklet_dir / f"creobook-{seed}-{edition.series.slug_prefix}.pdf"
        pages = pages_pdf_for(pdf)
        preview = preview_dir / f"{pdf.stem}.png"
        action = "aktualizuji" if edition.updates_existing else "nový produkt"
        print(f"{edition.source_name} → {name} (seed {seed}, {action})")
        if not args.no_generate:
            print(f"  generuji {pdf.name}")
            edition.series.generate(seed, pdf, label)
            print(f"  PDF: {pdf}")
        elif args.dry_run:
            print("  nahrání přeskočeno (--dry-run)")
            continue
        if not pdf.is_file() or not pages.is_file():
            raise SystemExit(
                f"Chybí {pdf.name} nebo {pages.name}. Spusťte skript bez --no-generate."
            )
        page = render_middle_page(pages, preview)
        print(f"  náhled: {preview.name}, stránka {page}")
        if args.dry_run:
            print("  nahrání přeskočeno (--dry-run)")
            continue
        source = shop.get_product(edition.source_id)
        file_url = shop.upload_pdf(pdf, f"{edition.series.slug_prefix}-{edition.number}.pdf")
        image_id = shop.upload_png(preview, f"{edition.series.slug_prefix}-{edition.number}.png")
        saved = shop.save_product(
            product_payload(source, edition, file_url, image_id, seed),
            edition.update_id,
        )
        print(f"  produkt: {saved.get('permalink')}")
    if coloring_job is not None:
        publish_coloring(
            shop,
            coloring_job,
            seed,
            dry_run=args.dry_run,
            no_generate=args.no_generate,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
