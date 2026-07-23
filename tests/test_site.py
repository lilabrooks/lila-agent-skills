from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
SITE_ROOT = ROOT / "docs"
SITE_INDEX = SITE_ROOT / "index.html"
REPOSITORY_URL = "https://github.com/lilabrooks/lila-agent-skills"


class AssetParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.local_assets: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        value = attributes.get("href") if tag in {"a", "link"} else None
        if tag == "script":
            value = attributes.get("src")
        if value and value.startswith("./"):
            self.local_assets.add(value)


def test_catalog_links_every_skill_package_once() -> None:
    html = SITE_INDEX.read_text(encoding="utf-8")
    skill_names = sorted(
        path.name
        for path in (ROOT / "skills").iterdir()
        if path.is_dir() and not path.name.startswith(".")
    )

    assert html.count('class="compact-card catalog-card skill-card"') == len(
        skill_names
    )
    for skill_name in skill_names:
        source_url = f"{REPOSITORY_URL}/blob/main/skills/{skill_name}/SKILL.md"
        assert html.count(source_url) == 1


def test_catalog_local_assets_exist() -> None:
    parser = AssetParser()
    parser.feed(SITE_INDEX.read_text(encoding="utf-8"))

    assert parser.local_assets
    for asset in parser.local_assets:
        path = urlsplit(asset).path
        target = SITE_ROOT / ("index.html" if path == "./" else path.removeprefix("./"))
        assert target.is_file(), f"missing local site asset: {asset}"


def test_catalog_keeps_detailed_guidance_in_canonical_docs() -> None:
    html = SITE_INDEX.read_text(encoding="utf-8")

    assert f"{REPOSITORY_URL}/blob/main/README.md#install-a-skill" in html
    assert f"{REPOSITORY_URL}/blob/main/README.md#agent-compatibility" in html
    assert 'href="./theme/LICENSE"' in html
