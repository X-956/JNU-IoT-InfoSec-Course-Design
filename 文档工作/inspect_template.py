from docx import Document
from pathlib import Path
from zipfile import ZipFile
import hashlib,json
ref=Path('物联网安全技术设计课程设计报告模板.docx')
d=Document(ref)
text=[]
for i,p in enumerate(d.paragraphs):
    text.append(f'{i}: {p.text}\n  {p._p.xml}')
Path('文档工作/template-xml.txt').write_text('\n'.join(text),'utf-8')
with ZipFile(ref) as z:
    inventory={n:dict(size=len(z.read(n)),sha256=hashlib.sha256(z.read(n)).hexdigest()) for n in z.namelist()}
Path('文档工作/template-parts.json').write_text(json.dumps(inventory,indent=2),'utf-8')
print('\n'.join(f'{i}: {p.text}' for i,p in enumerate(d.paragraphs)))
print('hash',hashlib.sha256(ref.read_bytes()).hexdigest())
print('sections',len(d.sections))
