from pathlib import Path
from pypdf import PdfReader
import re, uuid

DATA_DIR = Path(__file__).resolve().parents[2] / 'data'
DATA_DIR.mkdir(parents=True, exist_ok=True)
_documents: list[dict] = []

def ingest_pdf(filename: str, content: bytes) -> dict:
    safe = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)[:120]
    dest = DATA_DIR / f'{uuid.uuid4().hex[:8]}_{safe}'
    dest.write_bytes(content)
    reader = PdfReader(str(dest))
    added = 0
    for page_num, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ''
        paragraphs = [p.strip() for p in re.split(r'\n\s*\n|(?<=\.)\s{2,}', text) if p.strip()]
        if not paragraphs and text.strip(): paragraphs = [text.strip()]
        for i in range(0, len(paragraphs), 3):
            chunk = ' '.join(paragraphs[i:i+3])
            if len(chunk) < 20: continue
            _documents.append({'source_id': f'{dest.stem}-p{page_num}-c{i//3+1}', 'filename': filename, 'page': page_num, 'text': chunk})
            added += 1
    return {'filename': filename, 'pages': len(reader.pages), 'chunks_added': added, 'document_id': dest.stem}

def list_documents():
    by_name = {}
    for d in _documents: by_name[d['filename']] = by_name.get(d['filename'], 0) + 1
    return [{'filename': k, 'chunks': v} for k,v in by_name.items()]

def retrieve(query: str, k: int = 8) -> list[dict]:
    terms = set(re.findall(r'[a-z0-9]{2,}', query.lower()))
    scored = []
    for d in _documents:
        words = set(re.findall(r'[a-z0-9]{2,}', d['text'].lower()))
        score = len(terms & words) / max(1, len(terms))
        if score > 0: scored.append(({**d, 'score': round(score, 4)}, score))
    scored.sort(key=lambda x: x[1], reverse=True)
    return [x[0] for x in scored[:k]]
