"""The LEF texts per skill and level, read from docs/vaardigheden-niveaus-LEF.md (the one source,
CLAUDE.md: LEF texts are taken over literally). Used by the evaluation page (spec 039, F10).

The document has per skill a heading "## OC – Overzicht creëren" and per level "### Niveau 1 · <title>",
followed by bullets and an optional quote block "Extra context". Only that simple Markdown is turned
into HTML here; everything is escaped first.
"""

import html
import re
from functools import lru_cache
from pathlib import Path

from .paths import PROJECT_DIR
from .skills import SKILLS

SOURCE = PROJECT_DIR / "docs" / "vaardigheden-niveaus-LEF.md"

_SKILL = re.compile(r"^## (\w+) – ")
_LEVEL = re.compile(r"^### Niveau ([1-4]) · (.+)$")
_LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
_BOLD = re.compile(r"\*\*(.+?)\*\*")


def _inline(text: str) -> str:
    """Escape, then bold and links (only http(s); links inside the document become plain text)."""
    def link(match: re.Match) -> str:
        label, url = match.group(1).replace("\\*", "*"), match.group(2)
        if url.startswith(("http://", "https://")):
            return f'<a href="{url}" target="_blank" rel="noopener noreferrer">{label}</a>'
        return label
    escaped = html.escape(text, quote=False).replace("\\*", "*")
    return _BOLD.sub(r"<strong>\1</strong>", _LINK.sub(link, escaped))


def _to_html(lines: list[str]) -> str:
    out, in_list, quote = [], False, []

    def close_list():
        nonlocal in_list
        if in_list:
            out.append("</ul>")
            in_list = False

    def close_quote():
        if quote:
            out.append('<div class="lef-context">' + _to_html(quote) + "</div>")
            quote.clear()

    for line in lines:
        if line.startswith(">"):
            close_list()
            quote.append(line[1:].lstrip() if line != ">" else "")
            continue
        close_quote()
        stripped = line.strip()
        if stripped.startswith("- "):
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{_inline(stripped[2:])}</li>")
        elif stripped:
            close_list()
            out.append(f"<p>{_inline(stripped)}</p>")
        else:
            close_list()
    close_list()
    close_quote()
    return "".join(out)


def parse(text: str) -> dict[str, dict[int, dict]]:
    """{'OC': {1: {'title': ..., 'html': ...}, ...}, ...}"""
    result: dict[str, dict[int, dict]] = {}
    skill, level, title, body = None, None, "", []

    def flush():
        if skill and level:
            result.setdefault(skill, {})[level] = {"title": title, "html": _to_html(body)}

    for line in text.splitlines():
        if line.startswith("## "):
            flush()
            match = _SKILL.match(line)
            skill = match.group(1) if match and match.group(1) in SKILLS else None
            level, body = None, []
        elif line.startswith("### "):
            flush()
            match = _LEVEL.match(line)
            level, title, body = (int(match.group(1)), match.group(2).strip(), []) if match else (None, "", [])
        elif line.startswith("<a id="):
            continue
        elif level:
            body.append(line)
    flush()
    return result


@lru_cache(maxsize=1)
def texts(path: Path = SOURCE) -> dict[str, dict[int, dict]]:
    try:
        return parse(path.read_text(encoding="utf-8"))
    except OSError:
        return {}


def level_text(skill: str, level: str | int | None) -> dict | None:
    """The LEF text of one level (1-4), or None (startniveau has no text in LEF)."""
    try:
        number = int(level)
    except (TypeError, ValueError):
        return None
    return texts().get(skill, {}).get(number)
