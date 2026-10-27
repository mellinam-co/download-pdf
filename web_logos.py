"""HTML-SVG discovery and conservative SVG sanitization for trusted sites."""
import asyncio
import re
from urllib.parse import urljoin, urlsplit
from xml.etree import ElementTree as ET

import fitz
import httpx
from html.parser import HTMLParser

WEB_HOSTS = {'www.kavo.com', 'kavo.com',
             'www.germany.nsk-dental.com', 'germany.nsk-dental.com'}
SVG_NS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', SVG_NS)
ET.register_namespace('xlink', 'http://www.w3.org/1999/xlink')


def check_url(url):
    try:
        p = urlsplit(url)
        ok = (p.scheme == 'https' and p.hostname in WEB_HOSTS
              and p.port in (None, 443) and p.username is None
              and p.password is None and not p.fragment)
    except ValueError:
        ok = False
    if not ok:
        raise ValueError('Nur HTTPS-URLs der freigegebenen KaVo-/NSK-Domains erlaubt.')


async def fetch(url, max_bytes=2*1024*1024):
    """Bounded fetch. Every redirect must pass the same strict host allowlist."""
    try:
        async with asyncio.timeout(45):
            async with httpx.AsyncClient(timeout=15, follow_redirects=False,
                                         trust_env=False,
                                         headers={'User-Agent': 'Amber-Logo-Tools/3.0'}) as client:
                for _ in range(5):
                    check_url(url)
                    async with client.stream('GET', url) as r:
                        if r.status_code in (301, 302, 303, 307, 308):
                            location = r.headers.get('location')
                            if not location:
                                raise ValueError('Weiterleitung ohne Ziel.')
                            url = urljoin(url, location)
                            continue
                        r.raise_for_status()
                        data = bytearray()
                        async for chunk in r.aiter_bytes():
                            if len(data)+len(chunk) > max_bytes:
                                raise ValueError('Antwort zu groß (maximal 2 MB).')
                            data.extend(chunk)
                        return bytes(data), url
                raise ValueError('Zu viele Weiterleitungen.')
    except (httpx.HTTPError, TimeoutError):
        raise ValueError('Webabruf fehlgeschlagen oder Zeitlimit überschritten.') from None


class LogoHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.assets = []
        self.parents = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        parent_context = ' '.join(v for v in self.parents[-3:])
        context = str(attrs.get('class', '')) + ' ' + str(attrs.get('alt', '')) + ' ' + parent_context
        if tag in ('img', 'object', 'embed', 'a', 'link', 'source'):
            for key in ('src', 'data-src', 'data', 'href', 'srcset'):
                value = attrs.get(key)
                if not value:
                    continue
                values = [v.strip().split()[0] for v in value.split(',') if v.strip()] if key == 'srcset' else [value]
                self.assets.extend((v, context) for v in values)
        if tag not in ('img', 'link', 'source', 'embed', 'br', 'meta', 'input', 'hr', 'area', 'base', 'wbr'):
            self.parents.append(str(attrs.get('class', '')) + ' ' + str(attrs.get('id', '')))

    def handle_endtag(self, tag):
        if self.parents:
            self.parents.pop()

    def handle_startendtag(self, tag, attrs):
        depth = len(self.parents)
        self.handle_starttag(tag, attrs)
        del self.parents[depth:]


def discover(html, base_url):
    text = html.decode('utf-8', errors='replace') if isinstance(html, bytes) else html
    parser = LogoHTMLParser()
    parser.feed(text)
    candidates, seen = [], set()
    for value, context in parser.assets:
        url = urljoin(base_url, value)
        if not urlsplit(url).path.lower().endswith('.svg') or url in seen:
            continue
        seen.add(url)
        context = (url + ' ' + context).lower()
        score = (100 if 'logo' in context else 0) - (100 if any(s in context for s in ('favicon', 'icon', 'sprite')) else 0)
        try:
            check_url(url)
            allowed = True
        except ValueError:
            allowed = False
        candidates.append({'url': url, 'score': score, 'allowed': allowed})
    candidates.sort(key=lambda x: x['score'], reverse=True)
    # Preserve XML spelling and viewBox/clipPath capitalization from source HTML.
    inline = re.findall(r'<svg\b[^>]*>.*?</svg\s*>', text, flags=re.I | re.S)[:50]
    return candidates[:50], inline


TAGS = set('svg g defs path rect circle ellipse line polyline polygon clipPath mask '
           'linearGradient radialGradient stop use symbol title desc style text tspan'.split())
ATTRS = set('id class style viewBox width height x y x1 x2 y1 y2 cx cy r rx ry d points '
            'fill stroke stroke-width stroke-linecap stroke-linejoin stroke-miterlimit '
            'stroke-dasharray stroke-dashoffset fill-rule clip-rule clip-path mask '
            'opacity fill-opacity stroke-opacity transform preserveAspectRatio '
            'gradientUnits gradientTransform offset stop-color stop-opacity spreadMethod '
            'fx fy fr href font-family font-size font-weight text-anchor dx dy color '
            'maskUnits maskContentUnits clipPathUnits'.split())
LOCAL_URL = re.compile(r'url\(\s*[\'"]?(#[A-Za-z_][\w:.-]*)[\'"]?\s*\)', re.I)
PAINT = re.compile(r'(?P<key>(?<![\w-])(?:fill|stroke|stop-color|color))\s*:\s*(?P<value>[^;}]+)', re.I)


def safe_css(value):
    # Reject obfuscation, imports, external URLs and legacy executable CSS.
    if any(x in value.lower() for x in ('@', '\\', '/*', 'expression', 'javascript:', 'behavior', '-moz-binding')):
        raise ValueError('Nicht unterstützte oder unsichere SVG-CSS-Angabe.')
    rest = LOCAL_URL.sub('', value)
    if re.search(r'url\s*\(|https?:|data:', rest, re.I):
        raise ValueError('Externe SVG-Ressourcen werden nicht zugelassen.')


def recolor_css(css, color):
    def replace(m):
        val = m['value'].strip()
        if val.lower().replace('!important', '').strip() in ('none', 'transparent'):
            return m[0]
        if val.lower().startswith('url('):
            return m[0]  # Recolor gradient stops rather than references.
        return m['key'] + ':' + color + (' !important' if '!important' in val.lower() else '')
    return PAINT.sub(replace, css)


class NoDTDBuilder(ET.TreeBuilder):
    def doctype(self, name, pubid, system):
        raise ValueError('DTD und XML-Entities sind nicht zugelassen.')


def prepare_svg(data, color=None):
    if color is not None and not re.fullmatch(r'#[0-9a-fA-F]{6}', color):
        raise ValueError('Farbe als #RRGGBB oder null angeben.')
    try:
        root = ET.fromstring(data, parser=ET.XMLParser(target=NoDTDBuilder()))
    except Exception:
        raise ValueError('Ungültige SVG oder verbotene XML-Deklaration.') from None
    canonical = {n.lower(): n for n in TAGS | ATTRS}
    local = lambda name: canonical.get(name.rsplit('}', 1)[-1].lower(), name.rsplit('}', 1)[-1])
    if local(root.tag) != 'svg':
        raise ValueError('Die Datei ist keine SVG.')
    if sum(1 for _ in root.iter()) > 10000:
        raise ValueError('SVG ist zu komplex.')
    removed = 0
    for parent in list(root.iter()):
        for child in list(parent):
            if local(child.tag) not in TAGS:
                parent.remove(child)
                removed += 1
    for node in root.iter():
        # Normalize namespace, including SVG embedded directly in HTML.
        node.tag = '{' + SVG_NS + '}' + local(node.tag)
        for key in list(node.attrib):
            name = local(key)
            value = node.attrib[key]
            if key != name and not key.startswith('{'):
                del node.attrib[key]
                key = name
                node.set(key, value)
            if name not in ATTRS or (key.startswith('{') and name != 'href'):
                del node.attrib[key]
                continue
            if name == 'href' and not re.fullmatch(r'#[A-Za-z_][\w:.-]*', value):
                raise ValueError('Nur interne SVG-Referenzen erlaubt.')
            safe_css(value)
            if color and name in ('fill', 'stroke', 'stop-color', 'color'):
                if value.lower().strip() not in ('none', 'transparent') and not value.lower().startswith('url('):
                    node.set(key, color)
            elif color and name == 'style':
                node.set(key, recolor_css(value, color))
        if local(node.tag) == 'style':
            safe_css(node.text or '')
            if color:
                node.text = recolor_css(node.text or '', color)
    if color:
        root.set('fill', color)  # Default paint for paths without explicit color.
        root.set('color', color)
    if not any(local(n.tag) in ('path', 'rect', 'circle', 'ellipse', 'line', 'polyline', 'polygon', 'text', 'use') for n in root.iter()):
        raise ValueError('Keine unterstützten Vektorelemente gefunden.')
    svg = ET.tostring(root, encoding='utf-8', xml_declaration=True)
    if len(svg) > 2*1024*1024:
        raise ValueError('SVG überschreitet 2 MB.')
    try:
        with fitz.open(stream=svg, filetype='svg') as doc:
            p = doc[0]
            if p.rect.is_empty or p.rect.is_infinite:
                raise ValueError('Ungültige SVG-Größe.')
            zoom = min(3, 1200/max(p.rect.width, p.rect.height))
            # Gray preview backdrop keeps white brand logos visible.
            # The downloadable SVG itself retains its original transparency.
            with fitz.open('pdf', doc.convert_to_pdf()) as vector_pdf:
                with fitz.open() as backdrop:
                    page = backdrop.new_page(width=p.rect.width, height=p.rect.height)
                    page.draw_rect(page.rect, color=None, fill=(0.65, 0.65, 0.65))
                    page.show_pdf_page(page.rect, vector_pdf, 0)
                    png = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom)).tobytes('png')
    except Exception:
        raise ValueError('SVG konnte nicht für die Vorschau gerendert werden.') from None
    return svg, png, removed
