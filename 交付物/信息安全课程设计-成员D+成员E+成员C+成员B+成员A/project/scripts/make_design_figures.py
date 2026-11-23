from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import argparse

plt.rcParams['font.sans-serif']=['Microsoft YaHei','SimHei']
plt.rcParams['axes.unicode_minus']=False

def draw(out,name,boxes,edges,size=(9,5)):
    fig,ax=plt.subplots(figsize=size,dpi=180);ax.set(xlim=(0,10),ylim=(0,10));ax.axis('off')
    for i,(x,y,w,h,text) in enumerate(boxes):
        ax.add_patch(FancyBboxPatch((x-w/2,y-h/2),w,h,boxstyle='round,pad=.12',
                                   facecolor='#eef3f6',edgecolor='#426579',lw=1.2))
        ax.text(x,y,text,ha='center',va='center',fontsize=10)
    for a,b in edges:
        x,y,w,h,_=boxes[a];xx,yy,ww,hh,_=boxes[b]
        if abs(y-yy)>abs(x-xx):
            sign=1 if yy>y else -1;start=(x,y+sign*(h/2+.13));end=(xx,yy-sign*(hh/2+.13))
        else:
            sign=1 if xx>x else -1;start=(x+sign*(w/2+.13),y);end=(xx-sign*(ww/2+.13),yy)
        ax.annotate('',xy=end,xytext=start,arrowprops=dict(arrowstyle='->',lw=1.2,color='#426579'))
    fig.tight_layout();fig.savefig(out/name,bbox_inches='tight',facecolor='white');plt.close(fig)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);a=ap.parse_args()
    out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    draw(out,'architecture.png',[
        (2,8,3,1.2,'配置与离线选点\nini / NetworkX'),(7,8,3.8,1.2,'NetworkController\n邻接表、Dijkstra、失效事件'),
        (2,4.9,3,1.3,'NED 网络与传播链路\n24节点 / 40链路'),(7,4.9,3.8,1.3,'Satellite × 24\nCBR业务、下一跳表、转发'),
        (2,1.8,3,1.3,'Python分析与绘图\n汇总、守恒检查、路径重绘'),(7,1.8,3.8,1.3,'输出与界面\nsca / 包CSV / Qtenv')],[(0,1),(0,2),(1,3),(2,3),(3,5),(5,4)])
    draw(out,'algorithms.png',[
        (2.5,9,4.2,1,'载入带传播时延权重的邻接表'),(2.5,7,4.2,1,'对每个存活源执行Dijkstra\n跳过失效节点'),
        (2.5,5,4.2,1,'选择未访问且距离最小的节点\n松弛其存活邻居'),(2.5,3,4.2,1,'回溯prev，找出首跳\n写入目的→输出gate映射'),
        (2.5,1,4.2,1,'完成所有源路由表并下发'),
        (7.5,9,4,1,'t=40 s 失效事件\n列表 / 随机抽样'),(7.5,7,4,1,'标记逻辑失效并计算LCC\n失效节点停发、到达包丢弃'),
        (7.5,5,4,1,'恢复开：等待2 s并更新路由\n恢复关：保留旧路由'),(7.5,3,4,1,'数据包逐跳转发\n无路由或到达失效节点则丢弃'),
        (7.5,1,4,1,'包生成时间划分同批统计\n记录路径、终止时间与状态')],[(0,1),(1,2),(2,3),(3,4),(5,6),(6,7),(7,8),(8,9)],(10,7))

if __name__=='__main__':main()
