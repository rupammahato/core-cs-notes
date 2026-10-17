from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
import json
import re
import unicodedata
from pypdf import PdfReader

PARSER_VERSION = 'm23-nfc-pages-v1'


class InvalidDocument(ValueError):
    pass


class NeedsReview(InvalidDocument):
    pass


@dataclass(frozen=True)
class Segment:
    page: int
    text: str


def extract_document(name, data, max_bytes=65536, max_pages=3):
    if not name or '/' in name or '\\' in name or name in ('.', '..'):
        raise InvalidDocument('A display basename is required')
    if not isinstance(data, bytes) or not 0 < len(data) <= max_bytes:
        raise InvalidDocument('Invalid byte size')
    suffix = name.rsplit('.', 1)[-1].lower()
    if suffix in ('txt', 'md'):
        try:
            values = [(1, data.decode('utf-8', errors='strict'))]
        except UnicodeDecodeError as error:
            raise InvalidDocument('UTF-8 required') from error
    elif suffix == 'pdf':
        if not data.startswith(b'%PDF-'):
            raise InvalidDocument('PDF signature required')
        try:
            reader = PdfReader(BytesIO(data), strict=True)
            if reader.is_encrypted:
                raise InvalidDocument('Encrypted PDF not accepted')
            if not 1 <= len(reader.pages) <= max_pages:
                raise InvalidDocument('Page count exceeds policy')
            values = [(index + 1, page.extract_text() or '') for index, page in enumerate(reader.pages)]
        except InvalidDocument:
            raise
        except Exception as error:
            raise InvalidDocument('PDF parsing failed') from error
    else:
        raise InvalidDocument('Unsupported format')
    segments = []
    for page, text in values:
        text = unicodedata.normalize('NFC', text.replace('\r\n', '\n').replace('\r', '\n'))
        if '\x00' in text or len(text) > 50000:
            raise InvalidDocument('Invalid extracted content')
        if not text.strip():
            raise NeedsReview('No extractable text: inspect blank/scanned/OCR cases')
        segments.append(Segment(page, text))
    return segments


def make_chunks(tenant, document_id, version, segments, size=24, overlap=6):
    if type(size) is not int or type(overlap) is not int or not 0 <= overlap < size <= 200:
        raise ValueError('Require 0 <= overlap < size <= 200 words')
    config = json.dumps({'parser': PARSER_VERSION, 'size_words': size, 'overlap_words': overlap}, sort_keys=True)
    chunks = []
    for segment in segments:
        spans = list(re.finditer(r'\S+', segment.text))
        for start in range(0, len(spans), size - overlap):
            end = min(start + size, len(spans))
            left, right = spans[start].start(), spans[end - 1].end()
            text = segment.text[left:right]
            identity = json.dumps([tenant, document_id, version, config, segment.page, left, right, text], ensure_ascii=False)
            chunks.append({'chunk_id': sha256(identity.encode()).hexdigest(), 'page': segment.page,
                           'start': left, 'end': right, 'text': text})
            if end == len(spans):
                break
    return config, chunks
