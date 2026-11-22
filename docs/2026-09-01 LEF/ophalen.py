"""Fetch lef.hu.nl and write it as diff-friendly Markdown (one file per page).

Usage:
    python3 ophalen.py <output-folder> [--date YYYY-MM-DD] [--html <folder with saved pages>]

Only the Python standard library is used. Texts are copied literally; only the
markup is converted (bold, italic, underline, links, lists). Every paragraph and
list item is on its own line, so `diff -r` or `git diff --no-index` between two
snapshots shows exactly which texts changed.
"""

import argparse
import datetime
import html
import re
import sys
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

BASE = "https://lef.hu.nl"

# (file name, path on the site, title in the file). Order of the site's menu.
PAGES = [
    ("01-vaardigheden.md", "/", "Vaardigheden"),
    ("02-beroepsrollen.md", "/beroepsrollen", "Beroepsrollen"),
    ("03-beroepstaken-hboi.md", "/beroepstaken", "Beroepstaken / HBO-i"),
    ("04-beroepsproducten.md", "/beroepsproducten", "Beroepsproducten"),
    ("05-zo-gebruik-je-lef.md", "/leeswijzer", "Zo gebruik je LEF"),
]

# Codes and order from docs/vaardigheden-openict.md.
SKILL_CODES = {
    "Overzicht creëren": "OC",
    "Kritisch oordelen": "KO",
    "Juiste kennis ontwikkelen": "JKO",
    "Kwalitatief product maken": "KPM",
    "Plannen": "PL",
    "Boodschap delen": "BD",
    "Samenwerken": "SW",
    "Flexibel opstellen": "FO",
    "Pro-actief handelen": "PH",
    "Reflecteren": "RE",
}
SKILL_ORDER = list(SKILL_CODES)

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
        "source", "track", "wbr"}
SKIP = {"script", "style", "svg", "button", "select", "input", "nav", "noscript"}


# --- a minimal DOM -----------------------------------------------------------

class Node:
    def __init__(self, tag, attrs=None, parent=None):
        self.tag, self.attrs, self.parent, self.children = tag, dict(attrs or {}), parent, []

    def iter(self):
        yield self
        for c in self.children:
            if isinstance(c, Node):
                yield from c.iter()

    def find_all(self, pred):
        return [n for n in self.iter() if pred(n)]

    def find(self, pred):
        return next((n for n in self.iter() if pred(n)), None)

    def text(self):
        return "".join(c if isinstance(c, str) else c.text() for c in self.children)


class TreeBuilder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#root")
        self.cur = self.root

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs, self.cur)
        self.cur.children.append(node)
        if tag not in VOID:
            self.cur = node

    def handle_startendtag(self, tag, attrs):
        self.cur.children.append(Node(tag, attrs, self.cur))

    def handle_endtag(self, tag):
        n = self.cur
        while n is not self.root and n.tag != tag:
            n = n.parent
        if n is not self.root:
            self.cur = n.parent

    def handle_data(self, data):
        self.cur.children.append(data)


def parse(source):
    b = TreeBuilder()
    b.feed(source)
    return b.root


# --- Markdown rendering -----------------------------------------------------

def norm(s):
    return re.sub(r"\s+", " ", s)


def esc(s):
    return s.replace("\\", "\\\\").replace("*", "\\*").replace("_", "\\_")


def inline(node):
    """Inline Markdown for the children of node. Blank lines in the source are kept as '\n\n'."""
    out = []
    for c in node.children:
        if isinstance(c, str):
            parts = re.split(r"\n\s*\n", c)
            out.append("\n\n".join(esc(norm(p)) for p in parts))
            continue
        if c.tag in SKIP:
            continue
        inner = inline(c)
        if c.tag == "br":
            out.append("\n\n")
        elif not inner.strip():
            out.append(inner)
        elif c.tag in ("strong", "b"):
            out.append(wrap(inner, "**", "**"))
        elif c.tag in ("em", "i"):
            out.append(wrap(inner, "*", "*"))
        elif c.tag == "u":
            out.append(wrap(inner, "<u>", "</u>"))
        elif c.tag == "a" and c.attrs.get("href"):
            href = c.attrs["href"]
            if href.startswith("/"):
                href = BASE + href
            out.append(wrap(inner, "[", f"]({href})"))
        else:
            out.append(inner)
    return "".join(out)


def wrap(inner, left, right):
    lead = inner[: len(inner) - len(inner.lstrip(" "))]
    trail = inner[len(inner.rstrip(" ")):]
    return f"{lead}{left}{inner.strip(' ')}{right}{trail}"


def paragraphs(text):
    return [p.strip() for p in text.split("\n\n") if p.strip()]


BLOCK = {"p", "ul", "ol", "li", "div", "section", "h1", "h2", "h3", "h4", "h5", "h6",
         "details", "summary", "header", "main", "hr", "dialog", "table", "blockquote"}


class Renderer:
    """Renders blocks to a list of lines. Headings get `level + offset`."""

    def __init__(self, offset, hooks=None):
        self.offset = offset
        self.hooks = hooks or {}
        self.lines = []

    pending = None

    def heading(self, level, text):
        self.lines += ["", "#" * max(1, min(6, level)) + " " + norm(text).strip(), ""]
        if self.pending:
            self.lines += [self.pending, ""]
            self.pending = None

    def para(self, text):
        for p in paragraphs(text):
            self.lines += [p, ""]

    def block(self, node, depth=0):
        for hook, fn in self.hooks.items():
            if hook(node):
                fn(self, node)
                return
        if node.tag in SKIP or node.tag == "hr":
            return
        if re.fullmatch(r"h[1-6]", node.tag):
            self.heading(int(node.tag[1]) + self.offset, node.text())
        elif node.tag == "p":
            self.para(inline(node))
        elif node.tag in ("ul", "ol"):
            self.list(node, depth)
        elif node.tag in ("details", "summary") or node.tag in BLOCK or node.tag == "#root":
            self.children(node, depth)
        else:
            self.para(inline(node))

    def children(self, node, depth=0):
        buf = Node("#inline")
        for c in node.children:
            if isinstance(c, Node) and (c.tag in BLOCK or c.tag in SKIP):
                self.flush(buf)
                buf = Node("#inline")
                self.block(c, depth)
            else:
                buf.children.append(c)
        self.flush(buf)

    def flush(self, buf):
        text = inline(buf)
        if text.strip():
            self.para(text)

    def list(self, node, depth):
        n = 0
        for li in node.children:
            if not (isinstance(li, Node) and li.tag == "li"):
                continue
            n += 1
            marker = f"{n}." if node.tag == "ol" else "-"
            own = Node("#inline")
            own.children = [c for c in li.children if not (isinstance(c, Node) and c.tag in ("ul", "ol"))]
            text = " ".join(paragraphs(self.li_text(li, own)))
            if n == 1 and depth == 0 and self.lines and self.lines[-1] != "":
                self.lines.append("")
            self.lines.append("  " * depth + f"{marker} {text}")
            for sub in li.children:
                if isinstance(sub, Node) and sub.tag in ("ul", "ol"):
                    self.list(sub, depth + 1)
        if depth == 0:
            self.lines.append("")

    def li_text(self, li, own):
        return inline(own)

    def result(self):
        text = "\n".join(self.lines)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip() + "\n"


# --- page-specific structure ------------------------------------------------

def attr(name, value=None):
    return lambda n: name in n.attrs and (value is None or n.attrs[name] == value)


def page_vaardigheden(root):
    main = root.find(lambda n: n.tag == "main")
    r = Renderer(0)
    # Categories as the site shows them above the skill buttons.
    categories = []
    for sec in main.find_all(lambda n: n.tag == "section" and n.find(attr("data-filter-vaardigheid"))):
        h = sec.find(lambda n: n.tag == "h2")
        skills = [b.attrs["data-filter-vaardigheid"] for b in sec.find_all(attr("data-filter-vaardigheid"))]
        categories.append((norm(h.text()).strip(), skills))
    r.heading(2, "Indeling (zoals op de site)")
    for name, skills in categories:
        r.lines.append(f"- {name}: " + ", ".join(f"{SKILL_CODES.get(s, '?')} {s}" for s in skills))

    blocks = {d.attrs["data-vaardigheid"]: d for d in main.find_all(attr("data-vaardigheid"))}
    unknown = [s for s in blocks if s not in SKILL_CODES]
    if unknown:
        sys.exit(f"Onbekende vaardigheid op de site: {unknown}")
    stats = []
    for name in SKILL_ORDER:
        d = blocks.get(name)
        if d is None:
            r.heading(2, f"{SKILL_CODES[name]} – {name}")
            r.para("(Deze vaardigheid staat niet op de site.)")
            stats.append((SKILL_CODES[name], 0, []))
            continue
        sec = d.find(lambda n: n.tag == "section")
        r.heading(2, f"{SKILL_CODES[name]} – {norm(sec.find(lambda n: n.tag == 'h2').text()).strip()}")
        # Intro: the paragraphs before the level sections.
        intro = Node("#intro")
        for c in sec.children:
            if isinstance(c, Node) and (c.tag == "div" and c.find(attr("data-level"))):
                break
            if isinstance(c, Node) and c.tag in ("h2",):
                continue
            intro.children.append(c)
        r.children(intro)
        levels = [s for s in sec.find_all(lambda n: n.tag == "section" and "data-level" in n.attrs)]
        extras = {x.attrs["data-level"]: x for x in sec.find_all(lambda n: n.tag == "details")}
        for lv in levels:
            key = lv.attrs["data-level"]
            r.heading(3, norm(lv.find(lambda n: n.tag == "h3").text()).strip())
            body = Node("#lv")
            body.children = [c for c in lv.children
                             if not (isinstance(c, Node) and c.tag == "div" and c.find(lambda n: n.tag == "h3"))]
            # First <p> is the level title.
            first = next((c for c in body.children if isinstance(c, Node) and c.tag == "p"), None)
            if first is not None:
                r.lines += ["**" + inline(first).strip() + "**", ""]
                body.children.remove(first)
            r.children(body)
            ex = extras.pop(key, None)
            if ex is not None:
                summ = ex.find(lambda n: n.tag == "summary")
                r.heading(4, norm(summ.text()).strip())
                exbody = Node("#ex")
                exbody.children = [c for c in ex.children if c is not summ]
                r.children(exbody)
        if extras:
            sys.exit(f"Openklap-item zonder niveau bij {name}: {list(extras)}")
        has_extra = [lv.attrs["data-level"][-1] for lv in levels
                     if sec.find(lambda n, k=lv.attrs["data-level"]: n.tag == "details" and n.attrs.get("data-level") == k)]
        stats.append((SKILL_CODES[name], len(levels), has_extra))
    return r.result(), stats


def page_generic(root, title_offset=0, extra_hooks=None):
    main = root.find(lambda n: n.tag == "main")
    # Page-specific hooks first; then skip headers that only hold filter buttons.
    hooks = dict(extra_hooks or {})
    hooks[lambda n: n.tag == "header" and n.find(lambda m: m.tag == "button")] = lambda r, n: None
    r = Renderer(title_offset, hooks)
    r.children(main)
    return r


def page_beroepsrollen(root):
    def role(r, n):
        r.pending = f"`gilde: {n.attrs['data-guild']}`"
        r.children(n)
    layer_kind = {"primary-layer": "hoofdlaag", "secondary-layer": "extra laag"}

    def layers(r, n):
        # The site marks the role's layers only with a CSS class on each link.
        if r.lines and r.lines[-1] != "":
            r.lines.append("")
        for a in n.find_all(lambda m: m.tag == "a"):
            kind = layer_kind.get(a.attrs.get("class", "").strip(), "geen")
            r.lines.append(f"- {norm(a.text()).strip()}: {kind}")
        r.lines.append("")

    def overview(r, n):
        # Bachelor/Master grouping, shown on the site only as filter buttons.
        r.heading(2, "Indeling (zoals op de site)")
        for h in n.find_all(lambda m: m.tag == "h2"):
            box = h.parent
            codes = [b.attrs["data-filter-guild"] for b in box.find_all(attr("data-filter-guild"))]
            r.lines.append(f"- {norm(h.text()).strip()}: " + ", ".join(codes))
        r.lines.append("")

    return page_generic(root, 0, {lambda n: n.tag == "header" and n.find(attr("data-filter-guild")): overview,
                                  attr("data-guild"): role,
                                  lambda n: n.tag == "div" and n.attrs.get("class") == "hboi": layers}).result()


def page_beroepstaken(root):
    dialogs = {d.attrs["id"]: d for d in root.find_all(lambda n: n.tag == "dialog" and "lef-modal" in n.attrs)}
    used = []

    def render_modal(r, d):
        used.append(d.attrs["id"])
        first = True
        inner = d.find(lambda m: m.tag == "div") or d
        for c in inner.children:
            if isinstance(c, Node) and c.tag == "h2":
                r.heading(4 if first else 5, c.text())
                first = False
            elif isinstance(c, Node):
                r.block(c)
            elif c.strip():
                r.para(esc(norm(c)))

    def level(r, n):
        # Level text first, then the pop-up(s) that the level's button opens.
        r.children(n)
        for b in n.find_all(lambda m: m.tag == "button" and m.attrs.get("lef-modal")):
            d = dialogs.get(b.attrs["lef-modal"])
            if d is None:
                sys.exit(f"Pop-up {b.attrs['lef-modal']} niet gevonden")
            render_modal(r, d)

    def task(r, n):
        r.pending = f"`architectuurlaag: {n.attrs['data-architectuurlaag']} · activiteit: {n.attrs['data-activiteit']}`"
        r.children(n)

    r = page_generic(root, 0, {lambda n: n.tag == "dialog": lambda r, n: None,
                               lambda n: n.tag == "section" and "data-level" in n.attrs: level,
                               lambda n: n.tag == "div" and "data-architectuurlaag" in n.attrs: task})
    missing = set(dialogs) - set(used)
    if missing:
        sys.exit(f"Pop-ups niet geplaatst: {missing}")
    return r.result(), len(used)


def page_beroepsproducten(root):
    class R(Renderer):
        def li_text(self, li, own):
            guild = li.find(attr("data-guild-color"))
            if guild is not None:
                rest = Node("#rest")
                rest.children = [c for c in own.children if c is not guild]
                return f"{norm(guild.text()).strip()}: {inline(rest).strip()}"
            return inline(own)

    main = root.find(lambda n: n.tag == "main")
    r = R(0, {lambda n: n.tag == "header" and n.find(lambda m: m.tag == "button"): lambda r, n: None,
              lambda n: n.tag == "div" and "data-architectuurlaag" in n.attrs:
              lambda r, n: (setattr(r, "pending", f"`architectuurlaag: {n.attrs['data-architectuurlaag']} · activiteit: {n.attrs['data-activiteit']}`"), r.children(n))})
    r.children(main)
    return r.result()


def page_leeswijzer(root):
    return page_generic(root, 1).result()


# --- main --------------------------------------------------------------------

def fetch(path, html_dir):
    if html_dir:
        name = "index" if path == "/" else path.strip("/")
        return (Path(html_dir) / f"{name}.html").read_text(encoding="utf-8")
    req = urllib.request.Request(BASE + path, headers={"User-Agent": "lef-snapshot"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def header(title, path, date):
    return (f"# {title}\n\n"
            f"- Bron: {BASE}{path}\n"
            f"- Opgehaald: {date}\n"
            f"- Teksten letterlijk overgenomen; alleen de opmaak is omgezet naar Markdown.\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    ap.add_argument("--html")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    report = []
    for fname, path, title in PAGES:
        root = parse(fetch(path, args.html))
        if path == "/":
            body, stats = page_vaardigheden(root)
            report.append("Vaardigheden (niveaus / openklap-items):")
            for code, n, extra in stats:
                report.append(f"  {code:<4} {n} niveaus, {len(extra)} openklap-items (niveau {', '.join(extra) or '-'})")
        elif path == "/beroepsrollen":
            body = page_beroepsrollen(root)
        elif path == "/beroepstaken":
            body, n = page_beroepstaken(root)
            report.append(f"Beroepstaken: {n} pop-ups met extra toelichting")
        elif path == "/beroepsproducten":
            body = page_beroepsproducten(root)
        else:
            body = page_leeswijzer(root)
        (out / fname).write_text(header(title, path, args.date) + "\n" + body, encoding="utf-8")
        report.append(f"{fname}: {body.count(chr(10))} regels")
    print("\n".join(report))


if __name__ == "__main__":
    main()
