from io import BytesIO,StringIO
import csv
from openpyxl import Workbook
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject,NameObject,DecodedStreamObject
from ingestion import FIELDS

def csv_bytes(rows):
    stream=StringIO(newline='');writer=csv.writer(stream);writer.writerow(FIELDS);writer.writerows(rows)
    return stream.getvalue().encode('utf-8')

def row(identifier='a',name='Alpha',amount='12500',version='1',stamp='2026-10-14T12:00:00+05:30'):
    return [identifier,name,amount,version,stamp]

def xlsx_bytes(rows,*,extra_sheet=False):
    workbook=Workbook();sheet=workbook.active;sheet.title='Records';sheet.append(FIELDS)
    for values in rows:sheet.append(values)
    if extra_sheet:workbook.create_sheet('Other')
    stream=BytesIO();workbook.save(stream);workbook.close();return stream.getvalue()

def pdf_bytes(*,text=True,pages=1,encrypted=False):
    writer=PdfWriter()
    for _ in range(pages):
        page=writer.add_blank_page(width=612,height=792)
        if text:
            font=DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})
            page[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):font})})
            content=DecodedStreamObject();content.set_data(b'BT /F1 12 Tf 72 720 Td (fixture invoice) Tj ET')
            page[NameObject('/Contents')]=writer._add_object(content)  # Pinned test fixture writer only.
    if encrypted:writer.encrypt('public-fixture-password')
    stream=BytesIO();writer.write(stream);writer.close();return stream.getvalue()
