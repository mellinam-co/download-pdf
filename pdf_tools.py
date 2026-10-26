"""PDF-Vektoren isolieren; keine automatische Logoerkennung/OCR."""
import re
import fitz


def export_vectors(page, drawing_ids, color):
    if color is not None and not re.fullmatch(r'#[0-9a-fA-F]{6}', color):
        raise ValueError('Farbe als #RRGGBB angeben oder null für Originalfarben.')
    drawings = page.get_drawings()
    if not drawing_ids or len(drawing_ids) > 500:
        raise ValueError('1 bis 500 Pfad-IDs auswählen.')
    if any(type(i) is not int or not 0 <= i < len(drawings) for i in drawing_ids):
        raise ValueError('Ungültige Pfad-ID.')
    chosen = [drawings[i] for i in sorted(set(drawing_ids))]
    if sum(len(d['items']) for d in chosen) > 50000:
        raise ValueError('Auswahl zu komplex.')
    rgb = tuple(int(color[i:i+2], 16)/255 for i in (1, 3, 5)) if color else None
    bounds = fitz.Rect(chosen[0]['rect'])
    for d in chosen:
        bounds |= d['rect']
    margin = max([float(d.get('width') or 0) for d in chosen] + [0])/2 + 0.5
    bounds = fitz.Rect(bounds.x0-margin, bounds.y0-margin,
                       bounds.x1+margin, bounds.y1+margin) & page.rect
    if bounds.is_empty or bounds.width < 0.01 or bounds.height < 0.01:
        raise ValueError('Auswahl hat keine gültige Fläche.')
    out = fitz.open()
    try:
        target = out.new_page(width=page.rect.width, height=page.rect.height)
        for d in chosen:
            shape = target.new_shape()
            for item in d['items']:
                if item[0] == 'l': shape.draw_line(item[1], item[2])
                elif item[0] == 'c': shape.draw_bezier(*item[1:])
                elif item[0] == 're':
                    r = item[1]
                    # Winding orientation matters for holes in compound paths.
                    points = [r.tl, r.tr, r.br, r.bl, r.tl]
                    if len(item) > 2 and item[2] < 0: points = list(reversed(points))
                    shape.draw_polyline(points)
                elif item[0] == 'qu': shape.draw_quad(item[1])
                else: raise ValueError('Nicht unterstützter Pfadtyp.')
            fill = (rgb or d['fill']) if d.get('fill') is not None else None
            stroke = (rgb or d['color']) if d.get('color') is not None else None
            shape.finish(fill=fill, color=stroke,
                         width=d.get('width') or 0,
                         dashes=d.get('dashes'),
                         lineCap=max(d.get('lineCap') or (0,)),
                         lineJoin=d.get('lineJoin') or 0,
                         even_odd=d.get('even_odd', False),
                         closePath=bool(d.get('closePath')),
                         fill_opacity=(d.get('fill_opacity') if d.get('fill_opacity') is not None else 1),
                         stroke_opacity=(d.get('stroke_opacity') if d.get('stroke_opacity') is not None else 1))
            shape.commit()
        target.set_cropbox(bounds)
        svg = target.get_svg_image().encode('utf-8')
        preview = target.get_pixmap(matrix=fitz.Matrix(
            min(4, 1000/max(bounds.width, bounds.height)),
            min(4, 1000/max(bounds.width, bounds.height))), alpha=False).tobytes('png')
        return svg, preview
    finally:
        out.close()
