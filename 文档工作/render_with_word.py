"""Use native Word PDF export, then the skill's PNG rasterization pipeline.
Windows runtime has no bundled LibreOffice. Do not invoke desktop LibreOffice.
"""
from pathlib import Path
import importlib.util
import subprocess
import sys
import shutil

SKILL=Path(r'C:\Users\19739\.codex\plugins\cache\openai-primary-runtime\documents\26.1022.11436\skills\documents')
spec=importlib.util.spec_from_file_location('render_docx',SKILL/'render_docx.py')
renderer=importlib.util.module_from_spec(spec);spec.loader.exec_module(renderer)
source=Path(sys.argv[1]).resolve(); out=Path(sys.argv[2]).resolve();out.mkdir(parents=True,exist_ok=True)
pdf=out/(source.stem+'.pdf')
def quote(s):return "'"+str(s).replace("'","''")+"'"
script='''$ErrorActionPreference='Stop'
$word=New-Object -ComObject Word.Application
$word.Visible=$false
$word.DisplayAlerts=0
try {
 $doc=$word.Documents.Open(SOURCE,$false,$true)
 $doc.ExportAsFixedFormat(OUTPUT,17)
 $doc.Close(0)
} finally { $word.Quit() }
'''.replace('SOURCE',quote(source)).replace('OUTPUT',quote(pdf))
subprocess.run(['powershell','-NoProfile','-Command',script],check=True)
def converted(*args,**kwargs):return str(pdf),'Native Microsoft Word PDF export (Windows fallback)'
renderer.convert_to_pdf=converted
renderer.rasterize(str(source),str(out),120,False,False)
print(out)
