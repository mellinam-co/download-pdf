"""Optional helper for Amber run_code: save a complete MCP package dictionary."""
import base64
import hashlib
import io
from pathlib import Path
from PIL import Image


def save_package(package: dict, output_directory: str, manufacturer: str = 'logo'):
    """Only call with actual, unmodified structured MCP output, not reconstructed text."""
    import re
    if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}', manufacturer):
        raise ValueError('Ungültiger Dateiname.')
    svg = package['svg_text'].encode('utf-8')
    png = base64.b64decode(package['png_base64'], validate=True)
    for data, kind in ((svg, 'svg'), (png, 'png')):
        if hashlib.sha256(data).hexdigest() != package[f'{kind}_sha256']:
            raise ValueError(f'{kind}: SHA-256 stimmt nicht überein. Daten erneut übertragen.')
        if len(data) != package[f'{kind}_size_bytes']:
            raise ValueError(f'{kind}: Dateigröße stimmt nicht überein.')
    with Image.open(io.BytesIO(png)) as image:
        image.load()
        if image.format != 'PNG' or image.mode != 'RGBA' or not (0 < image.width <= 300 and 0 < image.height <= 36):
            raise ValueError('PNG-Anforderungen nicht erfüllt.')
        dimensions = image.size
    directory = Path(output_directory)
    directory.mkdir(parents=True, exist_ok=True)
    paths = {ext: directory / f'{manufacturer}.{ext}' for ext in ('svg', 'png')}
    # Do not overwrite existing files silently.
    if any(path.exists() for path in paths.values()):
        raise FileExistsError('Zieldatei existiert bereits. Anderen Namen verwenden.')
    paths['svg'].write_bytes(svg)
    paths['png'].write_bytes(png)
    return {'svg_path': str(paths['svg'].resolve()), 'png_path': str(paths['png'].resolve()),
            'width': dimensions[0], 'height': dimensions[1], 'hashes_verified': True}
