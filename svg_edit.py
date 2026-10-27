"""Explicit, version-bound SVG inspection and editing. No brand-color guessing."""
import re
from collections import Counter
from xml.etree import ElementTree as ET

from web_logos import NoDTDBuilder, prepare_svg

GRAPHICS = {'path', 'rect', 'circle', 'ellipse', 'line', 'polyline', 'polygon', 'text', 'use'}
PAINT_RE = re.compile(r'(?<![\w-])(fill|stroke|stop-color|color)\s*:\s*([^;}]+)', re.I)


def local(tag):
    return tag.rsplit('}', 1)[-1]


def parse(data):
    return ET.fromstring(data, parser=ET.XMLParser(target=NoDTDBuilder()))


def indexed(root):
    return {f'e{i}': node for i, node in enumerate(root.iter())}


def paint_key(value):
    value = value.strip().lower().replace('!important', '').strip()
    if re.fullmatch(r'#[0-9a-f]{3}', value):
        return '#' + ''.join(c*2 for c in value[1:])
    return {'white': '#ffffff', 'black': '#000000'}.get(value, value)


def inspect_svg(data, offset=0, limit=150):
    if offset < 0 or not 1 <= limit <= 200:
        raise ValueError('offset >= 0 und limit zwischen 1 und 200 erforderlich.')
    root = parse(data)
    nodes = indexed(root)
    reverse = {id(n): key for key, n in nodes.items()}
    parents = {id(c): p for p in root.iter() for c in p}
    paints = Counter()
    css = []
    elements = []
    for key, node in nodes.items():
        for attr in ('fill', 'stroke', 'stop-color', 'color'):
            if attr in node.attrib:
                paints[paint_key(node.attrib[attr])] += 1
        text = node.text or '' if local(node.tag) == 'style' else node.get('style', '')
        for _, value in PAINT_RE.findall(text):
            paints[paint_key(value)] += 1
        if local(node.tag) == 'style':
            css.append(text[:10000])
        if local(node.tag) in GRAPHICS | {'g', 'svg'}:
            parent = parents.get(id(node))
            elements.append({
                'element_id': key, 'tag': local(node.tag),
                'parent_id': reverse.get(id(parent)),
                'source_id': node.get('id'), 'class': node.get('class'),
                'attributes': {k: v[:500] for k, v in node.attrib.items() if k != 'd'},
                'path_data_length': len(node.get('d', '')),
                'text': ''.join(node.itertext())[:300] if local(node.tag) == 'text' else None,
            })
    return {'element_count': len(elements), 'elements': elements[offset:offset+limit],
            'next_offset': offset+limit if offset+limit < len(elements) else None,
            'declared_paints': dict(paints), 'stylesheets': css,
            'viewBox': root.get('viewBox'),
            'note': 'Farben sind deklarierte SVG-Werte, keine bestätigten Markenfarben. '
                    'Koordinatenattribute berücksichtigen keine geerbten Transformationen. '
                    'Keine automatische Slogan-Erkennung; Elemente visuell prüfen.'}


def validate_ids(nodes, ids):
    if len(ids) > 300 or any(key not in nodes for key in ids):
        raise ValueError('Ungültige oder zu viele Element-IDs.')


def isolate_svg(data, ids):
    """Preview selected artwork while retaining styles, ancestors and definitions."""
    root = parse(data)
    nodes = indexed(root)
    validate_ids(nodes, ids)
    if not ids:
        raise ValueError('Mindestens ein Element auswählen.')
    selected = {id(n) for key in ids for n in nodes[key].iter()}
    def walk(node, in_defs=False):
        in_defs = in_defs or local(node.tag) in ('defs', 'clipPath', 'mask', 'symbol')
        for child in list(node):
            if not in_defs and local(child.tag) in GRAPHICS and id(child) not in selected:
                node.remove(child)
            else:
                walk(child, in_defs)
    walk(root)
    return ET.tostring(root, encoding='utf-8')


def edit_svg(data, remove_ids, color_map, element_colors):
    root = parse(data)
    nodes = indexed(root)
    validate_ids(nodes, remove_ids + list(element_colors))
    if 'e0' in remove_ids:
        raise ValueError('SVG-Wurzel darf nicht entfernt werden.')
    for key in remove_ids:
        if local(nodes[key].tag) not in GRAPHICS | {'g'}:
            raise ValueError('Nur sichtbare Grafikelemente/Gruppen entfernbar.')
    for color in list(color_map.values()) + list(element_colors.values()):
        if not re.fullmatch(r'#[0-9a-fA-F]{6}', color):
            raise ValueError('Zielfarbe muss #RRGGBB sein.')
    mapping = {paint_key(k): v for k, v in color_map.items()}
    if any(k in ('none', 'transparent') or k.startswith('url(') for k in mapping):
        raise ValueError('Transparenz und Referenzen dürfen nicht global ersetzt werden.')
    def replace_css(css):
        return PAINT_RE.sub(lambda m: m[1]+':'+mapping.get(paint_key(m[2]), m[2])
                            + (' !important' if paint_key(m[2]) in mapping and '!important' in m[2].lower() else ''), css)
    removed_nodes = {id(n) for key in remove_ids for n in nodes[key].iter()}
    if any(id(nodes[key]) in removed_nodes for key in element_colors):
        raise ValueError('Entfernte Elemente können nicht gleichzeitig umgefärbt werden.')
    for node in root.iter():
        for attr in ('fill', 'stroke', 'stop-color', 'color'):
            if attr in node.attrib and paint_key(node.get(attr)) in mapping:
                node.set(attr, mapping[paint_key(node.get(attr))])
        if 'style' in node.attrib:
            node.set('style', replace_css(node.get('style')))
        if local(node.tag) == 'style':
            node.text = replace_css(node.text or '')
    # Explicit element recoloring applies to artwork descendants; none is preserved.
    for key, color in element_colors.items():
        if local(nodes[key].tag) not in GRAPHICS | {'g'}:
            raise ValueError('Nur Grafikelemente/Gruppen gezielt umfärben.')
        for node in nodes[key].iter():
            if local(node.tag) not in GRAPHICS:
                continue
            declared = {a.lower(): v for a, v in PAINT_RE.findall(node.get('style', ''))}
            fill = declared.get('fill', node.get('fill', 'black'))
            stroke = declared.get('stroke', node.get('stroke', 'none'))
            additions = []
            if paint_key(fill) not in ('none', 'transparent'):
                node.set('fill', color)
                additions.append(f'fill:{color}')
            if paint_key(stroke) not in ('none', 'transparent'):
                node.set('stroke', color)
                additions.append(f'stroke:{color}')
            node.set('style', node.get('style', '') + ';' + ';'.join(additions))
    for parent in list(root.iter()):
        for child in list(parent):
            if id(child) in removed_nodes:
                parent.remove(child)
    # Keep viewBox and layout; cropping is deliberately not automatic.
    return prepare_svg(ET.tostring(root, encoding='utf-8'))
