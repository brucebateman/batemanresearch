#!/usr/bin/env python3
"""Traditional Chinese (zh-Hant-TW) version of a static site, plus an EN / 中文 switch.

    python3 zh_hant.py extract   # list English segments still missing from zh-Hant.json
    python3 zh_hant.py build     # write zh/<page>.html and add the language switch to every page

Settings live in zh-Hant.json next to this script:
    root      folder holding the English pages ("." or "public")
    pages     English pages to translate
    switch_after  regex; the language switch is inserted right after its first match
    en_switch     false to leave the English pages untouched (their button then comes from site JS)
    strings   English segment -> Chinese. A segment is the inner HTML of a block that holds no
              other blocks, or an alt/title/aria-label/placeholder/meta text. Map a segment to
              itself to keep it in English (names, report titles).
    script    exact strings to replace inside inline <script> blocks
Untranslated segments stay in English; `extract` lists them and `build` reports the count.
"""
import copy, json, re, sys
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString, Tag, Comment

HERE = Path(__file__).resolve().parent
CONF = json.loads((HERE / 'zh-Hant.json').read_text(encoding='utf-8'))
ROOT = (HERE / CONF['root']).resolve()
OUT = ROOT / 'zh'

INLINE = {'a', 'abbr', 'b', 'br', 'code', 'em', 'i', 'img', 'kbd', 'mark', 'q', 's', 'small', 'span',
          'strong', 'sub', 'sup', 'time', 'u', 'wbr', 'svg', 'path', 'circle', 'rect', 'line', 'g', 'text', 'tspan'}
SKIP = {'script', 'style', 'noscript', 'svg', 'code', 'pre', 'template', 'iframe'}
ATTRS = ('alt', 'title', 'aria-label', 'placeholder')
META = {'description', 'og:title', 'og:description', 'twitter:title', 'twitter:description'}
SWITCH_CSS = (
    '.lang-switch{display:inline-flex;align-items:center;justify-content:center;min-width:44px;min-height:36px;'
    'padding:6px 12px;border:1px solid currentColor;border-radius:6px;font-size:14px;font-weight:600;'
    'line-height:1;text-decoration:none;white-space:nowrap;opacity:.85}'
    '.lang-switch:hover{opacity:1}'
    'html[lang^="zh"] body{word-break:normal;line-break:strict}'
    'html[lang^="zh"] .eyebrow,html[lang^="zh"] small{letter-spacing:.04em}'
)


def norm(s):
    return re.sub(r'\s+', ' ', s).strip()


def has_text(s):
    # Worth translating: has letters, not just an email, URL, phone, year or symbol.
    t = norm(s)
    if not re.search(r'[A-Za-z]{2,}', t):
        return False
    if re.fullmatch(r'[\w.+-]+@[\w.-]+|https?://\S+|[\w.-]+\.(com|org|net|io|ai)', t):
        return False
    return True


def is_block(tag):
    return isinstance(tag, Tag) and tag.name not in INLINE


def own_text(tag):
    return any(isinstance(c, NavigableString) and not isinstance(c, Comment) and c.strip() for c in tag.children)


def leaf_blocks(node):
    """Yield (kind, element) units. A unit is a block holding text and inline markup only
    (a paragraph, a heading), a standalone inline element such as a nav link or button,
    or loose text sitting between blocks."""
    mixed = any(is_block(c) for c in node.children)
    for child in list(node.children):
        if isinstance(child, Comment):
            continue
        if isinstance(child, NavigableString):
            if has_text(child) and mixed:
                yield 'text', child
            continue
        if child.name in SKIP or child.get('translate') == 'no':
            continue
        if any(is_block(d) for d in child.find_all(True)):
            yield from leaf_blocks(child)
        elif not has_text(child.get_text()):
            continue
        elif is_block(child) and not own_text(child) and len(child.find_all(True, recursive=False)) > 1:
            yield from leaf_blocks(child)      # a row of links or buttons: one unit each
        else:
            yield 'html', child


def inner(tag):
    return norm(tag.decode_contents())


def units(soup):
    """Every translatable unit as (key, setter)."""
    out = []
    if soup.title and has_text(soup.title.get_text()):
        out.append((norm(soup.title.get_text()), lambda v, t=soup.title: t.string.replace_with(v)))
    for m in soup.find_all('meta'):
        if (m.get('name') or m.get('property')) in META and m.get('content') and has_text(m['content']):
            out.append((norm(m['content']), lambda v, m=m: m.__setitem__('content', v)))
    body = soup.body or soup
    for kind, el in leaf_blocks(body):
        if kind == 'text':
            lead = re.match(r'\s*', str(el)).group(0)
            trail = re.search(r'\s*$', str(el)).group(0)
            out.append((norm(el), lambda v, el=el, a=lead, b=trail: el.replace_with(a + v + b)))
        else:
            out.append((inner(el), lambda v, el=el: (el.clear(), el.extend(
                list(BeautifulSoup(v, 'html.parser').contents)))))
    for el in body.find_all(True):
        if el.name in ('script', 'style'):
            continue
        for a in ATTRS:
            if el.get(a) and has_text(el[a]):
                out.append((norm(el[a]), lambda v, el=el, a=a: el.__setitem__(a, v)))
    return out


def soup_of(path):
    return BeautifulSoup(path.read_text(encoding='utf-8'), 'lxml')


def extract():
    missing, seen = {}, set()
    for page in CONF['pages']:
        for key, _ in units(soup_of(ROOT / page)):
            if key not in CONF['strings'] and key not in seen:
                seen.add(key)
                missing.setdefault(page, []).append(key)
    print(json.dumps(missing, ensure_ascii=False, indent=1))
    print(f'# {len(seen)} segments missing', file=sys.stderr)


def relink(soup, pages):
    """zh/ pages: translated pages stay side by side, everything else is one folder up."""
    names = {Path(p).name for p in pages}
    for el in soup.find_all(True):
        for a in ('href', 'src', 'srcset', 'poster', 'data-image', 'data-video', 'content'):
            v = el.get(a)
            if not v or a == 'content' and not (el.name == 'meta' and el.get('property') == 'og:image'):
                continue
            if a == 'srcset':
                el[a] = ', '.join(fix_url(part.strip(), names) for part in v.split(','))
            else:
                el[a] = fix_url(v, names)


def fix_url(v, names):
    first, _, rest = v.partition(' ')
    if re.match(r'^([a-z][a-z0-9+.-]*:|//|#|/)', first, re.I):
        return v
    path = re.split(r'[?#]', first)[0]
    if path in names:
        return v
    return '../' + v


MARK = re.compile(r'<!--lang-switch-->.*?<!--/lang-switch-->', re.S)


def add_switch(html, href, label, lang_name, alt_href, alt_lang):
    """Insert the switch with plain string edits, so the rest of the page keeps its formatting."""
    html = MARK.sub('', html)
    links = ''.join(f'<link rel="alternate" hreflang="{l}" href="{CONF["site"]}{u}">'
                    for l, u in (('en', alt_href[0]), ('zh-Hant', alt_href[1]), ('x-default', alt_href[0])))
    head = (f'<!--lang-switch--><style id="lang-switch-css">{SWITCH_CSS}{CONF.get("extra_css", "")}</style>'
            f'{links}<!--/lang-switch-->')
    html = html.replace('</head>', head + '</head>', 1)
    button = (f'<!--lang-switch--><a id="lang-switch" class="lang-switch" href="{href}" hreflang="{alt_lang}" '
              f'lang="{alt_lang}" aria-label="{lang_name}">{label}</a><!--/lang-switch-->')
    m = re.search(CONF['switch_after'], html)
    assert m, 'switch_after not found'
    return html[:m.end()] + button + html[m.end():]


def build():
    strings = {norm(k): v for k, v in CONF['strings'].items()}
    OUT.mkdir(exist_ok=True)
    total = missing = 0
    for page in CONF['pages']:
        src = ROOT / page
        en_url, zh_url = CONF['paths'].get(page, page), 'zh/' + page
        en_html = MARK.sub('', src.read_text(encoding='utf-8'))
        if CONF.get('en_switch', True):   # false: the English pages get their button from site JS
            src.write_text(add_switch(en_html, 'zh/' + page, '中文', '切換至繁體中文', (en_url, zh_url), 'zh-Hant'),
                           encoding='utf-8')

        zh = BeautifulSoup(en_html, 'lxml')
        for key, setter in units(zh):
            total += 1
            if key in strings:
                setter(strings[key])
            else:
                missing += 1
        for s in zh.find_all('script'):
            if s.string:
                text = s.string
                for en_s, zh_s in CONF.get('script', {}).items():
                    text = text.replace(en_s, zh_s)
                s.string.replace_with(text)
        zh.html['lang'] = 'zh-Hant-TW'
        relink(zh, CONF['pages'])
        for m in zh.select('meta[property="og:url"], link[rel="canonical"]'):
            m['content' if m.name == 'meta' else 'href'] = CONF['site'] + zh_url
        (OUT / page).write_text(add_switch(str(zh), '../' + page, 'EN', 'Switch to English', (en_url, zh_url), 'en'),
                                encoding='utf-8')
    print(f'{len(CONF["pages"])} pages, {total - missing}/{total} segments translated, {missing} left in English')


if __name__ == '__main__':
    {'extract': extract, 'build': build}[sys.argv[1]]()
