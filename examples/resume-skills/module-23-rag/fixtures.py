"""Generate tiny synthetic inputs for parser behavior; no user files are opened."""
from io import BytesIO
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject

NODE_TEXT = 'Node.js runs JavaScript outside the browser. It is a runtime, not a database. Event loop work must avoid blocking unrelated requests.'
REACT_TEXT = 'Stable keys preserve the identity of list items. React state follows the component type, position and key. Index keys can move a draft to another row.'


def make_pdf(pages, encrypted=False):
    writer = PdfWriter()
    for text in pages:
        page = writer.add_blank_page(width=612, height=792)
        if text:
            font = DictionaryObject({NameObject('/Type'): NameObject('/Font'), NameObject('/Subtype'): NameObject('/Type1'), NameObject('/BaseFont'): NameObject('/Helvetica')})
            page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'): DictionaryObject({NameObject('/F1'): writer._add_object(font)})})
            escaped = text.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
            stream = DecodedStreamObject()
            stream.set_data(('BT /F1 12 Tf 50 750 Td (' + escaped + ') Tj ET').encode('ascii'))
            page[NameObject('/Contents')] = writer._add_object(stream)
    if encrypted:
        writer.encrypt('fixture-password', algorithm='RC4-128')
    target = BytesIO()
    writer.write(target)
    return target.getvalue()
