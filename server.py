"""Token-protected MCP downloader. Files stay on this server."""
import asyncio
import os
import tempfile
import time
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4

import fitz
import httpx
from fastmcp import FastMCP
from fastmcp.server.auth import StaticTokenVerifier

TOKEN = os.environ['MCP_AUTH_TOKEN']
if len(TOKEN) < 32:
    raise RuntimeError('MCP_AUTH_TOKEN muss mindestens 32 Zeichen haben.')
ALLOWED_HOSTS = {'www.germany.nsk-dental.com', 'germany.nsk-dental.com'}
MAX_BYTES = 20 * 1024 * 1024
MAX_FILES = 20
TTL_SECONDS = 3600
STORAGE = Path(tempfile.mkdtemp(prefix='amber-pdfs-'))
LOCK = asyncio.Lock()
auth = StaticTokenVerifier(tokens={TOKEN: {
    'client_id': 'amber', 'sub': 'amber', 'scopes': ['pdf:download']
}})
mcp = FastMCP('PDF-Downloader', auth=auth)


def validate_url(url: str):
    try:
        p = urlsplit(url)
        valid = (p.scheme == 'https' and p.hostname in ALLOWED_HOSTS
                 and p.port in (None, 443) and p.username is None
                 and p.password is None and not p.fragment)
    except ValueError:
        valid = False
    if not valid:
        raise ValueError('Nur direkte HTTPS-URLs der freigegebenen NSK-Domains sind erlaubt.')


def cleanup():
    for path in STORAGE.glob('*.pdf'):
        if path.stat().st_mtime < time.time() - TTL_SECONDS:
            path.unlink(missing_ok=True)


@mcp.tool()
async def download_pdf(url: str) -> dict:
    """Download einer NSK-PDF. Die Datei-ID gilt NUR auf diesem MCP-Server.

    Keine automatische Uebergabe in Ambers Arbeitsbereich. Maximal 20 MB,
    keine Weiterleitungen. Fuer weitere Verarbeitung sind Tools auf diesem
    Server oder eine separate Dateitransfer-Integration erforderlich.
    """
    validate_url(url)
    async with LOCK:
        cleanup()
        if len(list(STORAGE.glob('*.pdf'))) >= MAX_FILES:
            raise ValueError('Temporärer Speicher voll. Später erneut versuchen.')
        data = bytearray()
        try:
            async with asyncio.timeout(45):
                async with httpx.AsyncClient(
                    follow_redirects=False, trust_env=False, timeout=15,
                    headers={'User-Agent': 'Amber-PDF-Downloader/1.0'},
                ) as client:
                    async with client.stream('GET', url) as response:
                        if 300 <= response.status_code < 400:
                            raise ValueError('Weiterleitung abgelehnt. Direkte PDF-URL verwenden.')
                        response.raise_for_status()
                        async for chunk in response.aiter_bytes():
                            if len(data) + len(chunk) > MAX_BYTES:
                                raise ValueError('Die PDF überschreitet 20 MB.')
                            data.extend(chunk)
        except (httpx.HTTPError, TimeoutError):
            raise ValueError('Download fehlgeschlagen oder Zeitlimit überschritten.') from None
        if not data.startswith(b'%PDF-'):
            raise ValueError('Die Antwort ist keine PDF-Datei.')
        try:
            with fitz.open(stream=bytes(data), filetype='pdf') as pdf:
                if pdf.needs_pass or pdf.page_count < 1:
                    raise ValueError('PDF nicht lesbar.')
                pages = pdf.page_count
        except Exception:
            raise ValueError('PDF ist ungültig oder passwortgeschützt.') from None
        file_id = uuid4().hex
        (STORAGE / f'{file_id}.pdf').write_bytes(data)
        return {'status': 'downloaded', 'file_id': file_id,
                'size_bytes': len(data), 'pages': pages,
                'storage': 'Nur auf diesem MCP-Server',
                'retention': 'Temporär; Bereinigung bei Aufrufen nach 1 Stunde; Neustarts können Dateien löschen.'}


if __name__ == '__main__':
    mcp.run(transport='http', host='0.0.0.0',
            port=int(os.environ.get('PORT', '8000')), path='/mcp')
