"""Package verified deliverables without mixing historical experiment runs."""
from pathlib import Path
from collections import Counter
from datetime import datetime
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '交付物'
REPORT = OUT / '课程设计报告_成员A.docx'
ARCHIVE = OUT / '信息安全课程设计_成员A_待验收.zip'

def sha(data):
    return hashlib.sha256(data).hexdigest()

files = {
    '课程设计报告_成员A.docx': REPORT,
    '提交前核对.md': OUT / '提交前核对.md',
    '组员任务分配.md': OUT / '组员任务分配.md',
}
for folder in ('src', 'simulations', 'scripts', 'configs',
               'results/final-20261105', 'results/screenshots'):
    for path in sorted((ROOT / 'project' / folder).rglob('*')):
        if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc':
            files[path.relative_to(ROOT).as_posix()] = path
for name in ('README.md', '验收演示.md', 'requirements.txt'):
    path = ROOT / 'project' / name
    files[path.relative_to(ROOT).as_posix()] = path

with zipfile.ZipFile(ARCHIVE, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
    for name, path in files.items():
        archive.write(path, name)
    archive.writestr('提交包说明.txt',
        '本包包含新版507次正式实验及报告、完整源码、配置、依赖和复现说明。\n'
        '旧版44+440次实验保留在原工作目录供追溯，本包只收录新版正式结果。\n'
        '五位成员的姓名、学号及报告分工已填入；待成员核对反馈及实际完成日期定稿。\n'
        '按当前安排以报告提交为主，演示说明作为工程附带资料。\n'
        '现有Qtenv截图为历史局部界面，完整路径图由实际包日志重绘。\n')

with zipfile.ZipFile(ARCHIVE) as archive:
    assert archive.testzip() is None, 'CRC check failed'
    for name, path in files.items():
        assert sha(archive.read(name)) == sha(path.read_bytes()), name
    runs = Counter()
    for name in archive.namelist():
        if name.startswith('project/results/final-20261105/') and name.endswith('.sca'):
            runs[name.split('/')[3]] += 1
    assert dict(runs) == {'checks': 1, 'raw': 66, 'sweep': 440}, runs
    file_count = len(archive.namelist())

template = ROOT / '物联网安全技术设计课程设计报告模板.docx'
assert sha(template.read_bytes()) == '29b4cd54f7b49da49f2a0debbed6bf77400eb02a14f3bbb385674483fa4a416e'
with zipfile.ZipFile(template) as original, zipfile.ZipFile(REPORT) as final:
    changed = {'word/document.xml', 'word/_rels/document.xml.rels', '[Content_Types].xml'}
    preserved = [name for name in original.namelist() if name not in changed]
    for name in preserved:
        assert original.read(name) == final.read(name), name

check = {
    'checked_at': datetime.now().isoformat(timespec='seconds'),
    'archive': ARCHIVE.name,
    'archive_sha256': sha(ARCHIVE.read_bytes()),
    'archive_bytes': ARCHIVE.stat().st_size,
    'file_count': file_count,
    'experiment_counts': dict(runs),
    'total_runs': sum(runs.values()),
    'report_sha256': sha(REPORT.read_bytes()),
    'report_pages_visually_reviewed': 18,
    'all_archived_files_match_sources': True,
    'crc_check': 'passed',
    'original_template_unchanged': True,
    'template_parts_preserved': len(preserved),
    'status': '五人资料及分工已填，待成员核对反馈和实际完成日期定稿',
}
(OUT / 'package-check.json').write_text(json.dumps(check, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(check, ensure_ascii=False, indent=2))
