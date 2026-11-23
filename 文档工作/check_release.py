from pathlib import Path
import sys,hashlib,json,math,subprocess
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'project/scripts'))
from analyze_results import parse_sca
project=ROOT/'project';final=project/'results/final-20261105'
manifest=json.loads((final/'manifest.json').read_text())
checked=[]
for path,digest in manifest['files'].items():
    if path.startswith(('src/','src\\','simulations/','simulations\\')):
        assert hashlib.sha256((project/path).read_bytes()).hexdigest()==digest,path
        checked.append(path)
matches=0
for group in ['raw','sweep']:
    for old in (project/'results'/group).glob('*.sca'):
        new=final/group/old.name
        assert new.exists(),old.name
        a,b=parse_sca(old),parse_sca(new)
        for metric in ['sent','received','dropped','pdr','pdr_after','lcc','components','mean_delay_ms','mean_hops']:
            if a[metric] is not None:
                assert math.isclose(a[metric],b[metric],rel_tol=1e-9,abs_tol=1e-7),(old.name,metric,a[metric],b[metric])
        matches+=1
assert matches==484,matches
for cmd in [
    [sys.executable,str(project/'scripts/analyze_results.py'),'--results',str(final),'--out',str(ROOT/'文档工作/should-not-exist.csv')],
    [sys.executable,str(project/'scripts/run_experiments.py'),'--suite','checks','--output',str(final)]]:
    r=subprocess.run(cmd,capture_output=True,text=True)
    assert r.returncode!=0,r.stdout
    assert 'No .sca files found' in r.stderr or 'Output already exists' in r.stderr,r.stderr
assert not (ROOT/'文档工作/should-not-exist.csv').exists()
for p in (project/'scripts').glob('*.py'):compile(p.read_text('utf-8'),str(p),'exec')
assert (project/'configs/IslNetwork.ned').read_bytes()==(project/'src/IslNetwork.ned').read_bytes()
result=dict(source_config_hash_matches=len(checked),legacy_runs_matching=matches,
            empty_input_rejected=True,existing_output_rejected=True,python_syntax='passed',
            generated_ned_matches=True)
(final/'release_checks.json').write_text(json.dumps(result,indent=2),'utf-8')
print(json.dumps(result,indent=2))
