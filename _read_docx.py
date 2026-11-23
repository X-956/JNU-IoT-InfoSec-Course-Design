import sys
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph


def iter_block_items(parent):
    from docx.oxml.ns import qn
    body = parent.element.body
    for child in body.iterchildren():
        if child.tag == qn('w:p'):
            yield Paragraph(child, parent)
        elif child.tag == qn('w:tbl'):
            yield Table(child, parent)


for path in sys.argv[1:]:
    print("=" * 20, path, "=" * 20)
    doc = Document(path)
    i = 0
    for block in iter_block_items(doc):
        if isinstance(block, Paragraph):
            text = block.text.strip()
            if text:
                i += 1
                print(f"[P{i}|{block.style.name}] {text}")
        else:
            i += 1
            print(f"[TABLE{i}]")
            for row in block.rows:
                cells = []
                seen = set()
                for c in row.cells:
                    if id(c._tc) in seen:
                        continue
                    seen.add(id(c._tc))
                    cells.append(c.text.replace("\n", " / ").strip())
                print(" | ".join(cells))
            print("[/TABLE]")
