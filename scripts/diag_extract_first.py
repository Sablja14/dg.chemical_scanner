import pandas as pd
import os
import sys
import requests

xlsx = os.path.join('..','pdf-files','excelchems.xlsx')
print('Reading', xlsx)
df = pd.read_excel(xlsx)
print('Rows:', len(df))
url = df.iloc[0]['Url']
print('First URL:', url)
try:
    r = requests.get(url, timeout=(5,20))
    r.raise_for_status()
    pdf_bytes = r.content
    print('Downloaded', len(pdf_bytes), 'bytes')
except Exception as e:
    print('Download error:', repr(e))
    sys.exit(2)

# Try PyMuPDF
try:
    import pymupdf as fitz
    print('pymupdf imported ok')
    doc = fitz.open(stream=pdf_bytes, filetype='pdf')
    print('pymupdf pages:', doc.page_count)
    text = []
    for i in range(doc.page_count):
        page = doc[i]
        t = page.get_text('text')
        print(f'page {i} len', len(t) if t else 0)
    doc.close()
except Exception as e:
    print('pymupdf failed:', repr(e))

# Try pypdf
try:
    import pypdf
    print('pypdf imported ok')
    reader = pypdf.PdfReader(pdf_bytes)
    print('pypdf pages:', len(reader.pages))
    for i,p in enumerate(reader.pages):
        try:
            t = p.extract_text()
            print(f'pypdf page {i} len', len(t) if t else 0)
        except Exception as e:
            print('pypdf page extract error', i, repr(e))
except Exception as e:
    print('pypdf failed:', repr(e))

print('diag script done')
