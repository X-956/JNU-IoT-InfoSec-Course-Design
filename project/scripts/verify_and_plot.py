"""Independently check terminal packet evidence and create report figures."""
from pathlib import Path
import argparse,csv,json,math,re
from collections import defaultdict
from statistics import mean,stdev
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
import networkx as nx
from analyze_results import parse_sca
from generate_topology import build_graph

plt.rcParams['font.sans-serif']=['Microsoft YaHei','SimHei','DejaVu Sans']
plt.rcParams['axes.unicode_minus']=False

def packets(path):
    with path.open(encoding='utf-8') as f:
        rows=list(csv.DictReader(f))
    for r in rows:
        for k in ['time','created','delay']:r[k]=float(r[k])
        for k in ['src','dst','seq','hops']:r[k]=int(r[k])
    return rows

def failed(path):
    return sorted(int(re.search(r'sat\[(\d+)\]',s).group(1))
        for s in path.read_text().splitlines()
        if re.match(r'scalar .*\.sat\[\d+\] failed 1$',s))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--dir',required=True);a=ap.parse_args()
    root=Path(a.dir);figdir=root/'figures';figdir.mkdir(exist_ok=True)
    checked=0
    for folder in ['raw','sweep','checks']:
        for sca in (root/folder).glob('*.sca'):
            s=parse_sca(sca);p=packets(sca.with_suffix('.packets.csv'))
            assert s['sent']==s['received']+s['dropped']==len(p),(sca,'conservation')
            assert len({(x['src'],x['seq']) for x in p})==len(p),(sca,'duplicate terminal event')
            rx=[x for x in p if x['status']=='received']
            g=build_graph() if s['planned_packets']==1440 else nx.cycle_graph(4)
            assert len(rx)==s['received']
            if rx:
                assert math.isclose(mean(x['delay'] for x in rx)*1000,s['mean_delay_ms'],abs_tol=1e-5)
                for x in rx:
                    ids=list(map(int,x['path'].split('-')))
                    assert ids[0]==x['src'] and ids[-1]==x['dst'] and len(ids)-1==x['hops']
                    assert all(g.has_edge(u,v) for u,v in zip(ids,ids[1:]))
            if s['sent_after'] is not None:
                cutoff=40.1 if s['config']=='CohortBoundary' else 10 if s['config']=='FourNodeFailure' else 40
                cohort=[x for x in p if x['created']>=cutoff]
                assert len(cohort)==s['sent_after']
                assert sum(x['status']=='received' for x in cohort)==s['received_after']
            checked+=1
    for seed in range(20):
        assert failed(root/'raw'/f'IslRandomFailure-{seed}.sca')==failed(root/'raw'/f'IslRandomNoRecovery-{seed}.sca')
    groups=defaultdict(list)
    for sca in (root/'raw').glob('*.sca'):groups[parse_sca(sca)['config']].append(parse_sca(sca))
    metrics=['sent','received','pdr','pdr_after','lcc','mean_delay_ms','mean_hops','goodput_kbps','service_completion_pct']
    stats={cfg:{'n':len(rs),**{m:{'mean':mean(r[m] for r in rs),'sd':stdev(r[m] for r in rs) if len(rs)>1 else 0}
        for m in metrics if all(r[m] is not None for r in rs)}} for cfg,rs in groups.items()}
    # Flow whose original path traverses failed S8 but endpoints survive.
    p=packets(root/'raw'/'IslReroute-0.packets.csv')
    old=next(x for x in p if x['created']==39 and x['status']=='received'
             and 8 in list(map(int,x['path'].split('-')))[1:-1])
    flow=[x for x in p if x['src']==old['src'] and x['dst']==old['dst']]
    new=next(x for x in flow if x['created']>=42 and x['status']=='received')
    evidence=dict(src=old['src'],dst=old['dst'],old_path=old['path'],new_path=new['path'],
        old_delay=old['delay'],new_delay=new['delay'],first_delivery=new['time'],
        failure_to_first_delivery_s=new['time']-40,route_update_s=42)
    # All initially affected, surviving endpoint flows; separate unreachable ones.
    affected={x['src']:x for x in p if x['created']==39 and x['status']=='received'
              and 8 in list(map(int,x['path'].split('-')))[1:-1] and x['src']!=8 and x['dst']!=8}
    recoveries=[]
    for src,x in sorted(affected.items()):
        eligible=[y for y in p if y['src']==src and y['created']>=42 and y['status']=='received']
        recoveries.append(dict(src=src,dst=x['dst'],first_delivery_s=eligible[0]['time'] if eligible else None,
            failure_to_delivery_s=eligible[0]['time']-40 if eligible else None))
    evidence['affected_surviving_flows']=recoveries
    fig,axs=plt.subplots(1,3,figsize=(12,3.8),dpi=180)
    cfgs=['IslBaseline','IslRandomFailure','IslFailure','IslNoRecovery']
    labels=['基线','随机 k=6','定向 k=6','定向不更新']
    for ax,m,title in zip(axs,['mean_delay_ms','goodput_kbps','service_completion_pct'],
                         ['成功送达包平均时延 / ms','有效吞吐量 / kbps（0–70 s）','原计划业务完成率 / %']):
        ys=[stats[c][m]['mean'] for c in cfgs];sd=[stats[c][m]['sd'] for c in cfgs]
        ax.bar(labels,ys,yerr=sd,capsize=3,color=['#427c9b','#77aa77','#c66b65','#999999'])
        ax.set_title(title,fontsize=10);ax.tick_params(axis='x',labelsize=8);ax.grid(axis='y',alpha=.2)
    fig.suptitle('通信性能：均值与样本标准差；时延仅针对成功送达包',fontsize=11)
    fig.tight_layout();fig.savefig(figdir/'performance.png');plt.close(fig)
    g=build_graph();pos={n:(n//8,-n%8) for n in g} # fixed below for readable slot order
    pos={n:(n//8,-(n%8)) for n in g}
    fig,axs=plt.subplots(1,3,figsize=(11,5.2),dpi=180)
    for ax,stage,path in zip(axs,['失效前：正常路径','40–42 s：旧路径中断','42 s 后：更新并绕路'],
                              [old['path'],old['path'],new['path']]):
        route=list(map(int,path.split('-')))
        def drawlinks(edges,color,width):
            for u,v in edges:
                wrap=abs(u-v)==7 and u//8==v//8
                u,v=sorted([u,v])
                ax.add_patch(FancyArrowPatch(pos[u],pos[v],arrowstyle='-',
                    connectionstyle='arc3,rad=0.12' if wrap else 'arc3,rad=0',
                    color=color,lw=width,zorder=1))
        drawlinks(g.edges,'#c9d0d5',1)
        nx.draw_networkx_nodes(g,pos,ax=ax,node_size=220,node_color=['#cb635d' if n==8 and ax!=axs[0] else '#8ab4c7' for n in g])
        nx.draw_networkx_labels(g,pos,ax=ax,font_size=7)
        drawlinks(zip(route,route[1:]),'#c66b65' if ax==axs[1] else '#267b55',3)
        ax.set_title(stage,fontsize=10);ax.text(.5,-.07,path,transform=ax.transAxes,ha='center',fontsize=8)
        ax.axis('off');ax.margins(.15)
    fig.suptitle(f'真实包日志重绘：S{old["src"]} → S{old["dst"]}，首个更新后包在 {new["time"]:.2f} s 送达',fontsize=11)
    fig.tight_layout();fig.savefig(figdir/'reroute_paths.png');plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,3.3),dpi=180)
    for status,color,marker in [('received','#267b55','o'),('failed_node','#c66b65','x'),('no_route','#c66b65','x')]:
        xs=[x['time'] for x in flow if 37<=x['created']<=46 and x['status']==status]
        ax.scatter(xs,[1 if status=='received' else 0]*len(xs),color=color,marker=marker,label=status)
    ax.axvline(40,color='#c66b65',ls='--',label='40 s 失效');ax.axvline(42,color='#427c9b',ls='--',label='42 s 更新')
    ax.set_yticks([0,1],['丢弃','送达']);ax.set_xlabel('包终止事件发生时间 / s');ax.set_ylim(-.4,1.5)
    ax.set_title(f'同一业务流事件时间线：恢复间隔 {new["time"]-40:.2f} s（含发包等待和传播）')
    ax.legend(fontsize=8,ncol=3);fig.tight_layout();fig.savefig(figdir/'reroute_timeline.png');plt.close(fig)
    result=dict(checked_runs=checked,paired_random_seeds=20,statistics=stats,recovery_evidence=evidence,
        boundary=parse_sca(root/'checks'/'CohortBoundary-0.sca'))
    (root/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
