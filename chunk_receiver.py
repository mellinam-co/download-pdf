"""Reference receiver for run_code. Uses persistent files, not Python session state."""
import base64
import hashlib
import json
import re
from pathlib import Path


def save_chunk(record, directory):
    transfer_id, kind, index = record['transfer_id'], record['file_type'], record['index']
    if not re.fullmatch(r'[0-9a-f]{32}', transfer_id) or kind not in ('svg','png'):
        raise ValueError('Invalid transfer identity')
    if type(index) is not int or not 0 <= index < record['chunk_count']:
        raise ValueError('Invalid index')
    text = re.sub(r'[ \t\r\n]', '', record['data_base64'])
    if len(text) != record['chars'] or len(text)>800:
        raise ValueError('Chunk length mismatch')
    if hashlib.sha256(text.encode('ascii')).hexdigest()!=record['chunk_sha256']:
        raise ValueError('Chunk hash mismatch')
    base64.b64decode(text,validate=True)
    target=Path(directory)/transfer_id
    target.mkdir(parents=True,exist_ok=True)
    stored=dict(record,data_base64=text)
    path=target/f'{kind}-{index:05d}.json'
    path.write_text(json.dumps(stored),encoding='utf-8')
    return str(path.resolve())


def assemble_file(manifest, kind, directory, destination):
    if kind not in ('svg','png') or not re.fullmatch(r'[0-9a-f]{32}', manifest['transfer_id']):
        raise ValueError('Invalid transfer identity')
    meta=manifest[kind];parts=[]
    for i in range(meta['chunk_count']):
        path=Path(directory)/manifest['transfer_id']/f'{kind}-{i:05d}.json'
        r=json.loads(path.read_text(encoding='utf-8'))
        if (r['transfer_id']!=manifest['transfer_id'] or r['file_type']!=kind
            or r['index']!=i or r['chunk_count']!=meta['chunk_count']
            or r['file_sha256']!=meta['sha256'] or r['file_size_bytes']!=meta['size_bytes']):
            raise ValueError('Mixed or inconsistent transfer')
        text=r['data_base64']
        if len(text)!=r['chars'] or hashlib.sha256(text.encode('ascii')).hexdigest()!=r['chunk_sha256']:
            raise ValueError(f'Changed chunk: {i}')
        parts.append(text)
    joined=''.join(parts)
    if len(joined)!=meta['base64_chars']:
        raise ValueError('Full Base64 length mismatch')
    data=base64.b64decode(joined,validate=True)
    if len(data)!=meta['size_bytes'] or hashlib.sha256(data).hexdigest()!=meta['sha256']:
        raise ValueError('Full file hash/size mismatch')
    target=Path(destination)
    if target.exists():raise FileExistsError('Choose a new output filename')
    target.write_bytes(data)
    return {'path':str(target.resolve()),'bytes':len(data),'verified':True}
