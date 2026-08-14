import re
from pathlib import Path


TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "app" / "templates"
STATIC_JS_DIR = Path(__file__).resolve().parents[1] / "app" / "static" / "js"


def defined_functions(source: str) -> set[str]:
    return set(re.findall(r"function\s+([A-Za-z_$][\w$]*)", source))


def test_every_card_handler_is_defined_on_the_pages_that_render_cards() -> None:
    """A card button whose handler is missing throws on click, silently.

    The renderer emits onclick names, and each page has to supply them. That
    contract is invisible: nothing fails to load, nothing logs, the button
    just does nothing when pressed.
    """
    renderer = (STATIC_JS_DIR / "card-renderer.js").read_text()
    shared = (STATIC_JS_DIR / "shared.js").read_text()

    handlers = set(re.findall(r'onclick="([A-Za-z_$][\w$]*)', renderer))
    assert handlers, "no handlers found, the check would pass vacuously"

    available_everywhere = defined_functions(shared)

    missing: list[str] = []
    for template in sorted(TEMPLATES_DIR.glob("*.html")):
        markup = template.read_text()
        if "card-renderer.js" not in markup:
            continue
        available = available_everywhere | defined_functions(markup)
        for handler in sorted(handlers - available):
            missing.append(f"{template.name}: {handler}")

    assert not missing
