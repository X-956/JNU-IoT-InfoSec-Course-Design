"""Run from an OMNeT++ shell with Python available; preserve old outputs."""
from pathlib import Path
import argparse
import subprocess
import sys
import json
import hashlib

ROOT=Path(__file__).resolve().parents[1]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--suite',choices=['basic','sweep','checks','all'],default='all')
    ap.add_argument('--output',required=True)
    a=ap.parse_args()
    out=Path(a.output).resolve()
    if out.exists(): ap.error('Output already exists; choose a new directory to preserve prior data')
    exe=ROOT/('isl.exe' if (ROOT/'isl.exe').exists() else 'isl')
    if not exe.exists(): ap.error('Build executable first')
    out.mkdir(parents=True)
    jobs=[]
    if a.suite in ('basic','all'):
        for cfg,n in [('FourNodeBaseline',1),('FourNodeFailure',1),('IslBaseline',1),
                      ('IslFailure',20),('IslRandomFailure',20),('IslNoRecovery',1),
                      ('IslRandomNoRecovery',20),('IslReroute',1),('IslRerouteOff',1)]:
            jobs += [('omnetpp.ini',cfg,s,'raw') for s in range(n)]
    if a.suite in ('checks','all'):
        jobs += [('omnetpp.ini','CohortBoundary',0,'checks')]
    if a.suite in ('sweep','all'):
        jobs += [('batch.ini',f'{mode}K{k}',s,'sweep')
                 for k in range(2,13) for mode in ['Target','Random'] for s in range(20)]
    for i,(ini,cfg,seed,group) in enumerate(jobs,1):
        folder=out/group;folder.mkdir(exist_ok=True)
        stem=folder/f'{cfg}-{seed}'
        cmd=[str(exe),'-u','Cmdenv','-f',ini,'-c',cfg,f'--seed-set={seed}',
             f'--output-scalar-file={stem.as_posix()}.sca',
             f'--**.controller.traceFile={json.dumps(stem.as_posix()+".packets.csv")}',
             '--cmdenv-event-banners=false']
        with stem.with_suffix('.log').open('w',encoding='utf-8') as log:
            subprocess.run(cmd,cwd=ROOT/'simulations',stdout=log,stderr=subprocess.STDOUT,check=True)
        if i%25==0 or i==len(jobs): print(f'{i}/{len(jobs)} runs completed',flush=True)
    manifest=dict(suite=a.suite,runs=len(jobs),jobs=jobs,
        files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
               for base in ['src','simulations','scripts'] for p in (ROOT/base).rglob('*')
               if p.is_file() and '__pycache__' not in str(p)})
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    for group in ['raw','sweep','checks']:
        if (out/group).exists():
            subprocess.run([sys.executable,str(ROOT/'scripts/analyze_results.py'),
                '--results',str(out/group),'--out',str(out/f'{group}_summary.csv')],check=True)

if __name__=='__main__':main()
