"""Small, independently verifiable Base64 responses; immutable file snapshots."""
import base64
import hashlib
import math

CHUNK_CHARS = 800
CHUNK_BYTES = CHUNK_CHARS // 4 * 3


def file_manifest(data):
    return {'size_bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
            'base64_chars': 4 * math.ceil(len(data)/3),
            'chunk_count': max(1, math.ceil(len(data)/CHUNK_BYTES)),
            'chunk_chars_max': CHUNK_CHARS}


def make_chunk(data, transfer_id, file_type, index):
    meta = file_manifest(data)
    if type(index) is not int or not 0 <= index < meta['chunk_count']:
        raise ValueError('Abschnittsindex außerhalb des gültigen Bereichs.')
    start = index * CHUNK_BYTES
    raw = data[start:start+CHUNK_BYTES]
    encoded = base64.b64encode(raw).decode('ascii')
    return {'transfer_id': transfer_id, 'file_type': file_type,
            'index': index, 'chunk_count': meta['chunk_count'],
            'data_base64': encoded, 'chars': len(encoded),
            'chunk_sha256': hashlib.sha256(encoded.encode('ascii')).hexdigest(),
            'file_sha256': meta['sha256'], 'file_size_bytes': meta['size_bytes']}
