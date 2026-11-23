"""Read per-run scalars. New cohort metrics; legacy files remain readable."""
from __future__ import annotations
import argparse
import csv
import re
from pathlib import Path

SCALAR_RE = re.compile(r'^scalar\s+(\S+)\s+(\S+)\s+([-\d.eE+]+)\s*$')

def parse_sca(path: Path) -> dict:
    totals = dict.fromkeys(['sent', 'received', 'dropped', 'delaySum', 'hopSum'], 0.)
    controller = {}
    config = path.name.split('-')[0]
    for line in path.read_text(encoding='utf-8', errors='replace').splitlines():
        if line.startswith('attr configname '):
            config = line.split(maxsplit=2)[2].strip('"')
        m = SCALAR_RE.match(line)
        if m:
            module, key, val = m.groups()
            if '.sat[' in module and key in totals: totals[key] += float(val)
            elif module.endswith('.controller'): controller[key] = float(val)
    sent, received = totals['sent'], totals['received']
    duration = controller.get('observationDuration')
    planned = controller.get('plannedPackets')
    return dict(file=path.name, config=config, sent=int(sent), received=int(received),
        dropped=int(totals['dropped']), pdr=100*received/sent if sent else None,
        pdr_after=controller.get('pdrAfterFailure'),
        after_definition='generation_cohort' if 'sentAfterFailureCohort' in controller else 'legacy_cutoff',
        sent_after=controller.get('sentAfterFailureCohort'),
        received_after=controller.get('receivedAfterFailureCohort'),
        lcc=controller.get('lccAfterFailure'), components=controller.get('componentsAfterFailure'),
        failed=controller.get('failedCount'),
        route_update_delay_s=controller.get('routeUpdateDelay',controller.get('recoveryTime')),
        mean_delay_ms=1000*totals['delaySum']/received if received else None,
        mean_hops=totals['hopSum']/received if received else None,
        observation_s=duration,
        goodput_kbps=received*1024*8/duration/1000 if duration else None,
        planned_packets=planned,
        service_completion_pct=100*received/planned if planned else None)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--results',required=True)
    ap.add_argument('--out',required=True)
    a=ap.parse_args()
    paths=sorted(Path(a.results).glob('*.sca'))
    if not paths: ap.error('No .sca files found; point --results at raw/ or sweep/')
    rows=[parse_sca(p) for p in paths]
    if any(r['sent']==0 for r in rows): ap.error('Input includes a run with zero sent packets')
    out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    print(f'{len(rows)} runs -> {out}')
if __name__=='__main__':main()
