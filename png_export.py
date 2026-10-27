"""Render final transparent PNGs. Preview backdrops are never used."""
import io
import math

import fitz
from PIL import Image


def render_logo_png(svg: bytes, trim_transparent: bool = True, padding: int = 1):
    if type(padding) is not int or not 0 <= padding <= 5:
        raise ValueError('padding muss zwischen 0 und 5 Pixeln liegen.')
    with fitz.open(stream=svg, filetype='svg') as doc:
        page = doc[0]
        w, h = page.rect.width, page.rect.height
        if not math.isfinite(w+h) or min(w, h) <= 0:
            raise ValueError('Ungültige SVG-Abmessungen.')
        zoom = min(8, 2400/max(w, h))
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=True)
        image = Image.open(io.BytesIO(pix.tobytes('png'))).convert('RGBA')
    bounds = image.getchannel('A').getbbox()
    if bounds is None:
        raise ValueError('SVG enthält keinen sichtbaren Inhalt.')
    if trim_transparent:
        image = image.crop(bounds)
    available_w, available_h = 300-2*padding, 36-2*padding
    scale = min(available_w/image.width, available_h/image.height)
    target = (max(1, min(available_w, round(image.width*scale))),
              max(1, min(available_h, round(image.height*scale))))
    image = image.resize(target, Image.Resampling.LANCZOS)
    if padding:
        canvas = Image.new('RGBA', (image.width+2*padding, image.height+2*padding), (0,0,0,0))
        canvas.paste(image, (padding, padding))
        image = canvas
    if image.width > 300 or image.height > 36:
        raise ValueError('Interner Größenfehler.')
    output = io.BytesIO()
    image.save(output, format='PNG', optimize=True)
    return output.getvalue(), {'width': image.width, 'height': image.height,
                             'mode': image.mode, 'alpha_channel': True,
                             'transparent_border_pixels': padding,
                             'trim_transparent': trim_transparent}
