from pathlib import Path
from copy import deepcopy
from zipfile import ZipFile, ZIP_DEFLATED
import hashlib, json, re, textwrap
from docx import Document
from docx.shared import Pt,Cm,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH,WD_TAB_ALIGNMENT,WD_TAB_LEADER
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT=Path(__file__).resolve().parents[1]
REF=ROOT/'物联网安全技术设计课程设计报告模板.docx'
assert hashlib.sha256(REF.read_bytes()).hexdigest()=='29b4cd54f7b49da49f2a0debbed6bf77400eb02a14f3bbb385674483fa4a416e'
OUT=ROOT/'交付物';OUT.mkdir(exist_ok=True)
RESULT=ROOT/'project/results/final-20261105'
V=json.loads((RESULT/'verification.json').read_text('utf-8'))
d=Document(REF)
original=list(d.paragraphs)
def setfont(run,size=12,bold=False,font='宋体'):
    run.font.name=font;run.font.size=Pt(size);run.font.bold=bold;run.font.color.rgb=RGBColor(0,0,0)
    run._element.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'),font)
def replace(p,text):
    rpr=deepcopy(p.runs[0]._r.rPr) if p.runs and p.runs[0]._r.rPr is not None else None
    p.clear();r=p.add_run(text)
    if rpr is not None:r._r.insert(0,rpr)
    r.font.color.rgb=RGBColor(0,0,0)
def para(text='',size=12,bold=False,center=False,indent=True):
    p=d.add_paragraph();p.paragraph_format.line_spacing=1.25
    p.paragraph_format.space_before=Pt(0);p.paragraph_format.space_after=Pt(6)
    p.paragraph_format.first_line_indent=Pt(24 if indent and not center else 0)
    p.alignment=WD_ALIGN_PARAGRAPH.CENTER if center else WD_ALIGN_PARAGRAPH.LEFT
    setfont(p.add_run(text),size,bold);return p
def heading(text,level=1):
    p=para(text,bold=level==1,indent=False)
    p.paragraph_format.space_before=Pt(8);p.paragraph_format.space_after=Pt(8)
    p.paragraph_format.keep_with_next=True
    # Real outline levels without modifying the template's styles.xml.
    el=OxmlElement('w:outlineLvl');el.set(qn('w:val'),str(level-1));p._p.get_or_add_pPr().append(el)
    return p
def page():
    p=d.add_paragraph();p.paragraph_format.space_after=Pt(0);p.paragraph_format.space_before=Pt(0)
    p.paragraph_format.line_spacing=1;p.add_run().add_break(__import__('docx').enum.text.WD_BREAK.PAGE)
    setfont(p.runs[0],1)
def table(headers,rows,widths=None):
    t=d.add_table(rows=1,cols=len(headers));t.autofit=False
    widths=widths or [14.65/len(headers)]*len(headers)
    for c,w in zip(t.columns,widths):c.width=Cm(w)
    for i,h in enumerate(headers):t.rows[0].cells[i].text=str(h)
    for row in rows:
        cells=t.add_row().cells
        for i,x in enumerate(row):cells[i].text=str(x)
    for j,row in enumerate(t.rows):
        pr=row._tr.get_or_add_trPr();pr.append(OxmlElement('w:cantSplit'))
        if j==0:pr.append(OxmlElement('w:tblHeader'))
        for c,w in zip(row.cells,widths):
            c.width=Cm(w)
            for p in c.paragraphs:
                p.paragraph_format.line_spacing=1.25;p.paragraph_format.space_after=Pt(3);p.paragraph_format.space_before=Pt(3)
                for r in p.runs:setfont(r,12,j==0)
            tcpr=c._tc.get_or_add_tcPr();b=OxmlElement('w:tcBorders')
            for side in ['top','left','bottom','right']:
                e=OxmlElement('w:'+side);e.set(qn('w:val'),'single');e.set(qn('w:sz'),'4');e.set(qn('w:color'),'999999');b.append(e)
            tcpr.append(b)
    para('',indent=False).paragraph_format.space_after=Pt(0)
    return t
def figure(name,caption,width=14.6):
    p=para('',center=True);p.paragraph_format.space_after=Pt(2)
    p.add_run().add_picture(str(RESULT/'figures'/name),width=Cm(width))
    cp=para(caption,center=True);cp.paragraph_format.keep_with_next=False
def code(text):
    for line in text.splitlines():
        for s in textwrap.wrap(line,64,replace_whitespace=False,drop_whitespace=False,
                              subsequent_indent='    ',break_long_words=False,break_on_hyphens=False) or ['']:
            p=para(s,indent=False);p.paragraph_format.space_after=Pt(0);p.paragraph_format.line_spacing=1.25
def val(cfg,key):return V['statistics'][cfg][key]['mean']

# Preserve the real cover and edit its slots; expand long title over two lines.
replace(original[4],'设计题目：基于 OMNeT++ 的导航卫星星间\n通信网络抗毁性与通信性能仿真')
for r in original[4].runs:setfont(r,14)
original[4].paragraph_format.left_indent=Cm(2.54)
original[4].paragraph_format.first_line_indent=Pt(0)
original[4].paragraph_format.line_spacing=1.25
for attr in ['leftChars','firstLineChars','hangingChars']:
    original[4]._p.pPr.ind.attrib.pop(qn('w:'+attr),None)
replace(original[5],'专    业：物联网工程')
replace(original[6],'班    级：物联网2301')
replace(original[7],'小组组长：成员A  学号：学号A')
for p,(name,sid) in zip(original[8:12],[('成员B','学号B'),('成员C','学号C'),('成员D','学号D'),('成员E','学号E')]):
    replace(p,f'小组成员：{name}  学号：{sid}')
for p in original[7:12]:
    for r in p.runs:setfont(r,14)
replace(original[12],'指导教师：胡凯')
replace(original[13],'2026 年［待填］月［待填］日')
for p in original[14:]:p._p.getparent().remove(p._p)

page()
para('本小组各成员工作分工汇总',size=18,bold=True,center=True)
para('课题：基于 OMNeT++ 的导航卫星星间通信网络抗毁性与通信性能仿真',indent=False)
table(['成员及学号','负责模块','具体分工'],[
    ['成员B\n学号B','需求分析与总体方案','完善目的、课题描述与需求；核对拓扑、参数和系统结构。'],
    ['成员C\n学号C','程序设计与算法说明','核对节点、控制器、路由与恢复流程；完善流程图及代码说明。'],
    ['成员D\n学号D','实验场景与测试说明','核对基线、随机、定向与恢复配置；完善测试步骤及调试说明。'],
    ['成员E\n学号E','数据统计与结果分析','核对投递率、时延、吞吐及连通性图表；完善分析结论。'],
    ['成员A\n学号A','总结与报告整合','完善总结、参考文献和源码附录；合并修改并统一格式。']], [3.4,4.1,7.15])
table(['时间与状态','记录'],[
    ['项目开始','2026年10月27日'],['本次实验与核验','2026年11月5日'],
    ['课程设计完成日期','［实际完成时填写］'],['教师验收','［日期、结论待填写］']], [4.5,10.15])
para('提交材料包括课程设计报告和完整源代码；原始数据、参数配置、复现说明及图表随工程提供。',indent=False)

page()
para('目        录',size=22,bold=True,center=True)
toc=[('1. 课程设计目的',4),('2. 课程设计课题描述和需求分析',4),('3. 课程设计报告内容',5),
 ('3.1 课程设计任务分析',5),('3.2 设计方案与概要设计',6),('3.3 详细设计与核心算法',7),
 ('3.4 交互与运行界面',9),('3.5 安全评估、性能结果与调试',10),('4. 总结及体会',15),
 ('参考文献',15),('附录A 核心路由源程序',16),('附录B 包统计与转发源程序',17),('附录C 配置与复现入口',18)]
for text,num in toc:
    p=para(f'{text}\t{num}',size=14,bold=True,indent=False)
    p.paragraph_format.tab_stops.add_tab_stop(Cm(14.4),WD_TAB_ALIGNMENT.RIGHT,WD_TAB_LEADER.DOTS)
    p.paragraph_format.space_after=Pt(10)

page()
heading('1. 课程设计目的')
para('围绕信息安全中的可用性，使用OMNeT++建立导航卫星星间通信的简化虚拟网络，完成拓扑建模、业务生成、逐跳转发、节点失效注入与路由更新，观察局部故障如何影响端到端服务。通过同一拓扑下的对照实验，区分随机失效与定向破坏的影响，并量化恢复机制的收益及其边界。')
para('实践目标是形成从需求、算法、原型到数据分析和演示的完整过程。重点掌握离散事件仿真、带权最短路径、介数中心性选点和可复现实验方法，避免仅凭界面变色判断通信是否恢复。[1–3]')
heading('2. 课程设计课题描述和需求分析')
para('课题采用3轨道面、每面8节点的静态抽象星间网络。卫星导航学习材料提供应用背景，实验对象为星间通信可用性。模型将节点离线、被破坏或转发能力失效统一抽象为节点逻辑不可用，评估正常通信、随机失效、自适应介数定向攻击和路由更新开关四类情况。')
table(['需求','实现与判定依据'],[
 ['构建虚拟网络','4节点最小网络及24节点星间网络，可编译运行'],
 ['通信性能测试','收发量、投递率、平均时延、跳数、有效吞吐量'],
 ['安全性评估','同样失效数量下比较随机与定向攻击；统计LCC和分区'],
 ['展示与交互','Qtenv运行控制、节点状态、包路径及实验对照图'],
 ['可复现交付','源码、ini、种子、原始sca、包日志和自动分析脚本']], [3.6,11.05])
para('实验在自建仿真环境内完成，安全性结论限定为本模型的可用性与抗毁性。模型未引入真实轨道运动、射频信道、定位解算、链路排队或容量限制；所得结果不直接代表实际卫星系统性能。')

page()
heading('3. 课程设计报告内容')
heading('3.1 课程设计任务分析',2)
para('首先用4节点环验证发包、路由、转发、失效和计数，再扩展至24节点。固定拓扑与流量参数，以失效选择方式、失效数量及路由更新开关为自变量。随机失效运行20个种子；定向节点集合固定，重复运行用于检查确定性。')
table(['环境','版本或作用'],[['Windows 11 x64','运行及文档制作'],['OMNeT++ 6.4.0','自带clang64工具链、Cmdenv与Qtenv'],
 ['Python 3.12','批量运行、原始结果分析与绘图'],['NetworkX 3.3','离线生成拓扑与自适应介数攻击序列'],
 ['NumPy / pandas / Matplotlib','1.26.4 / 2.2.2 / 3.9.2']], [5,9.65])
table(['参数','正式24节点实验取值'],[['节点与链路','24节点；同面环24条，异面16条双向链路'],
 ['链路传播时延','同面70 ms，异面120 ms；ned.DelayChannel'],
 ['业务','每节点1包/s，1024 B，目的为(nodeId+12)%24'],
 ['时间','1–60 s发包（含60 s），仿真至70 s排空'],
 ['失效与更新','40 s节点失效，42 s路由更新；对照组关闭更新'],
 ['扫描','k=2…12；随机/定向各20次，共440次']], [4.2,10.45])
para('2026年11月5日从更新后的源码独立编译，完成66次基础及配对实验、440次扫描和1次非整数失效边界检查，共507次运行。所有结果使用独立文件保存。')

page()
heading('3.2 设计方案与概要设计',2)
para('系统分为配置与离线选点、网络及节点、集中式控制器和数据分析四部分。NED定义连接及传播时延；Satellite维护下一跳表并处理业务包；NetworkController读取实际gate连接，计算路由和连通性，调度失效与更新事件；Python生成攻击序列并分析仿真输出。')
figure('architecture.png','图1 系统功能结构与数据流')
para('24节点按3列轨道面、8行序号显示。同面节点构成环，相邻轨道面中同序号节点互连，最外两面之间没有直接跨面边。每条连接双向可用，路由代价为传播时延之和。图7中的完整网络用于展示真实包路径。')
para('集中式控制器假设掌握全局连接状态，更新后直接将下一跳下发到各节点。2 s等待是人为设定的检测和更新等待，不模拟分布式协议泛洪、路由计算耗时或控制信令竞争。节点失效时保留NED连线，逻辑上禁止发包并丢弃到达包。')
para('批量实验使用Cmdenv保证高效重复；Qtenv提供开始、暂停、逐事件及加速运行。两种界面使用同一套C++模块和ini参数，正式统计来自原始标量及包日志。')

page()
heading('3.3 详细设计与核心算法',2)
para('路由使用Dijkstra：对每个存活源初始化距离，反复取距离最小的未访问节点，按传播时延松弛存活邻居；再沿prev回溯确定首跳。实现以线性扫描选最小节点，单源O(V²+E)，全源O(V³+VE)，适合本实验24节点规模。[2]')
figure('algorithms.png','图2 路由计算与失效恢复事件流程',14.2)
para('定向攻击在离线图中每次删除当前无权介数最大的节点，然后重新计算介数；并列时优先度数，再取较小编号。[3–4] k=6序列为8、12、1、5、19、23。仿真在40 s一次性将前k个节点置为失效，并非在运行中逐个攻击。路由使用时延权重，攻击选点使用无权介数，二者定义分别固定。')

page()
heading('数据结构与指标定义',2)
table(['结构','主要字段及用途'],[
 ['DataPacket','src、dst、seq、hops、createdAt、path，追踪源流及路径'],
 ['邻接表adj','vector<map<int,double>>，保存邻居及秒单位边权'],
 ['下一跳nextHop','目的编号→输出gate；无项即无可用路径'],
 ['节点状态','failed标志；sent/received/dropped及delaySum/hopSum'],
 ['终止包日志','time、created、src、dst、seq、status、path、delay、hops']], [4.0,10.65])
para('全时段PDR = 接收包数 / 实际发送包数 ×100%。失效后PDR按生成时间分组：分子与分母都只取createdAt≥failureTime的同一批包。失败、不可达和成功终止事件均记录唯一的(src,seq)，仿真排空后可逐包核对。')
para('平均时延为成功送达包的Σ(到达时间−生成时间)/接收数；平均跳数为hopSum/接收数。失败包不计入时延，需同时观察投递率，防止把高丢包造成的样本筛选误读为时延改善。')
para('有效吞吐量 = 接收数×1024×8 /70 s /1000，单位kbps。分母是包含发包前空闲与末尾排空的完整0–70 s观察窗，各24节点场景口径一致，不代表链路容量。业务完成率 = 接收数 /1440 ×100%，以无故障时24×60个计划包为基准，纳入失效源停发带来的服务损失。')
para('LCC为失效后最大连通分量节点数；分区数只在存活节点诱导子图中计算。路由更新等待为配置值2 s；业务恢复间隔按原路径受影响、两端存活的流，取路由更新后生成的首个成功包到达时刻减失效时刻，含发包等待和传播。无可用路径时标为不可恢复，不填0。')
para('重复实验报告均值及样本标准差SD。当前正式指标为上述统计；包日志保留扩展分析所需样本，本报告不将未计算的P95或攻击效率列为完成结果。')

page()
heading('3.4 交互与运行界面',2)
para('运行入口选择配置名称。IslBaseline显示正常通信；IslRandomFailure和IslFailure在40 s将对应节点变色；IslReroute只使S8失效，便于观察存活流在42 s后改道。Qtenv工具栏支持运行、暂停与加速，检查节点可查看状态和计数。')
p=para('',center=True);p.add_run().add_picture(str(ROOT/'project/results/screenshots/qtenv_failure.png'),width=Cm(14.6))
para('图3 Qtenv操作界面局部（已有定向攻击运行截图）',center=True)
para('图3用于说明界面布局和颜色，底部节点未完整入镜；完整24节点及恢复前后路径见图7的日志重绘。节点变红表示逻辑不可用，仍可见连线不表示还能转发。')
code('../isl.exe -u Qtenv -c IslReroute --seed-set=0\n  --output-scalar-file=../results/demo/IslReroute-0.sca')
para('上述两行展示同一条命令，执行时合为一行，并先创建results/demo目录。演示沿用正式40 s失效、60 s停发、70 s结束的参数；全部统计以运行完成后的文件为准。先展示基线，再看随机与定向对照，最后展示S8失效的恢复路径及包事件时间线。')

page()
heading('3.5 安全评估、性能结果与调试',2)
para('以下结果来自本次507次真实数据包级仿真。k=6时随机和定向各20次，其他确定性对照按表注明。百分比为实际结果，±为样本SD。')
table(['场景 / 次数','发送','接收均值','全程PDR','失效后PDR'],[
 ['基线 / 1','1440','1440','100.00%','—'],
 ['随机 k6 / 20','1314','1189.70','90.54±2.13%','67.12±7.41%'],
 ['定向 k6 / 20','1314','974','74.12%','10.05%'],
 ['定向不更新 / 1','1314','936','71.23%','0.00%'],
 ['随机不更新 / 20','1314','986.40','75.07±2.76%','13.33±9.61%']], [3.3,1.6,2.4,3.6,3.75])
figure('pdr_random_vs_targeted.png','图4 相同失效数量下的投递率与连通性（误差棒SD）')
para('相同k=6下，定向攻击的失效后PDR比随机失效低57.06个百分点。随机失效LCC为17.85±0.49，定向攻击LCC为9且分为2块，说明该拓扑对关键跨面中继集合更敏感。失效后低投递率同时含路径被切断和源/目的离线的影响。')
para('20组随机恢复配对使用相同seed，逐组失效集合一致；更新使失效后PDR由13.33%升至67.12%，平均增加53.78个百分点。定向k=6只由0升至10.05%，说明路由更新无法弥补已分区和端点失效的损失。')

page()
heading('失效规模扫描与安全分析',2)
figure('sweep_pdr_lcc.png','图5 k=2…12扫描，每点20次（误差棒SD）')
para('定向攻击k=5→6时，失效后PDR从67.67%降至10.05%；k≥7时当前24条固定业务流的失效后PDR为0。随机失效随k增加渐进退化，k=12时仍为13.65%。这里的0表示本实验业务未成功送达，不等于剩余图完全没有任何可通信节点对。')
para('自适应选点每删除一节点就重算介数，会继续寻找剩余图中的关键中继，因此比一次性按初始介数排序更能体现持续针对性。该结论依赖当前3×8拓扑与固定业务矩阵，不证明所有星间网络具有相同临界点。')
para('定向配置的20次重复结果完全相同，SD为0，原因是失效集合、CBR时刻和路由并列决策固定。随机种子只改变随机失效抽样；不能将确定性重复解释为对所有攻击不确定性的统计覆盖。')
para('全时段PDR在部分大k下回升，并非安全性增强。失效前已有936包完成交付，失效节点随后停止发包，使实际发送分母随k增大而缩小；同时幸存业务结构变化。因此主安全指标采用失效后PDR，并同时给出发送量、接收量、LCC和相对计划业务完成率。')
para('防护启示是保护关键中继和跨面连接，考虑额外路径冗余与失效检测；本实现只评估了重新计算路径的收益，没有实现备份链路或节点修复，也未测量其实际效果。')

page()
heading('通信性能与理论结果对照',2)
table(['场景','均值时延/ms','平均跳数','有效吞吐/kbps','业务完成率'],[
 ['基线','440.00','5.333','168.52','100.00%'],
 ['随机 k6','445.04±9.44','5.377','139.23±3.28','82.62%\n±1.95'],
 ['定向 k6','443.12','5.359','113.99','67.64%'],
 ['定向不更新','440.00','5.333','109.54','65.00%']], [2.7,3.1,2.6,3.5,2.75])
figure('performance.png','图6 通信性能对比（按运行求均值；误差棒SD）')
para('基线理论检查：16条目的位于相邻轨道面的流各经过4条同面和1条跨面边，时延4×70+120=400 ms、5跳；8条跨越两个轨道面的流为4条同面及2条跨面边，时延520 ms、6跳。故均值(16×400+8×520)/24=440 ms，平均跳数128/24=5.333，与仿真一致。')
para('无故障时每节点60包，接收1440包；按70 s窗口计算吞吐1440×8192/70/1000=168.52 kbps。失效后吞吐下降主要来自不可达及源停发；由于无排队和序列化，本实验不能据此评价拥塞控制或最大链路吞吐。')
para('定向不更新组时延仍为440 ms，是因为成功样本集中在失效前；它的业务完成率仅65%。因此“时延较低”必须与交付量联合解释，不能单独作为恢复效果的证据。')

page()
heading('可见的恢复过程与包级证据',2)
figure('reroute_paths.png','图7 S8失效前后真实路径重绘，所有24节点完整展示')
figure('reroute_timeline.png','图8 S11→S23的包终止事件时间线')
para('IslReroute中仅S8失效，存活图仍连通（LCC=23）。S11→S23原路径为11–10–9–8–15–23；更新后为11–12–13–14–15–23。两条路径均5跳、400 ms，恢复通过改变中继绕过故障，而非降低时延。')
para('40 s失效、42 s更新，42 s生成的首个新路径包于42.40 s到达，恢复间隔为2.40 s。6条原路径受S8影响且两端存活的流均恢复，间隔为2.40–2.52 s，均值2.42 s。该定义含发包节拍和传播，不能视作协议收敛时间。')
para('单节点场景更新开启/关闭的失效后PDR分别为93.17%与69.57%。目的S8离线的业务仍不能送达，S8自身停发；这些服务损失保留在统计中。图7—8由本次包CSV重绘，不是Qtenv截图。')

page()
heading('调试问题、验证与模型限制',2)
table(['问题','处理与实际验证'],[
 ['路径与生成器不一致','修复batch.ini输出路径；NED使用同一生成器输出到src和configs；重新编译通过'],
 ['恢复时间误命名','固定值改为routeUpdateDelay；真实包日志另给首包恢复间隔'],
 ['截点接收混入旧包','按createdAt同批统计；40.1 s失效检查：460发、432收，PDR=93.913%'],
 ['原指标设计超出实现','统一为无队列DelayChannel模型，删除带宽、队列和处理时延的完成声明'],
 ['空目录静默汇总','分析无sca时明确报错；运行输出目录已存在则拒绝覆盖'],
 ['演示与正式数据混写','演示独立目录，正式数据保留各配置、seed、日志与manifest']], [4.4,10.25])
para('验证结果：507次运行逐次满足sent=received+dropped，且每个已发送包恰有一个终止记录；成功包路径由实际邻接边构成，首尾与源目的吻合，跳数与路径边数一致。日志重算的接收数、均值时延及失效后同批计数均与标量一致。20个随机种子的恢复开关对照失效节点完全相同。')
para('40.1 s检查在失效时已有960个包生成、936个到达。截点差法会把450个后续到达计为失效后接收，其中18个属于失效前生成；同批法正确接收数432。该检查证明新统计在跨界在途包情形下仍保持一致。')
para('理论设计与实践差异：静态图无法覆盖轨道可见性随时间变化；节点离线只模拟可用性故障；没有物理层、带宽、队列、分布式控制信令和检测误差。早期方案中的10 Mbps、50包队列、2 ms/跳及P95等未作为本版已实现指标。本报告全部结论限定在当前参数和业务矩阵内。')

page()
heading('4. 总结及体会')
para('本课设完成了可运行的星间通信网络原型、随机与定向失效、带权路由更新以及可复现的数据分析。基线计数、时延和跳数与理论推导一致；k=6定向攻击使网络分区，恢复只能救回有限业务；随机失效下路由更新有更明显收益。单节点案例进一步把“节点失效—旧路径丢包—更新—新路径首包到达”的过程落实为可追溯日志。')
para('工程实践表明，指标定义与边界事件和算法本身同样重要。原先把等待参数叫作恢复时间、以时间截点差统计包数，容易产生错误解释；引入生成时间同批统计、终止事件记录和固定计划业务分母后，能更准确区分网络故障、路径绕行及业务需求变化。')
para('后续可沿动态拓扑、链路失效、队列与容量约束扩展，并比较冗余链路或分布式路由。但每次扩展都应重新确定自变量、统计窗口与可验证预期，避免用抽象模型直接推断真实系统。')
heading('参考文献')
refs=[
 '[1] OpenSim Ltd., OMNeT++ Simulation Manual, Version 6.4.0, 2026, https://doc.omnetpp.org/omnetpp/manual/（本机安装包同名手册）。',
 '[2] Dijkstra E W, A note on two problems in connexion with graphs, Numerische Mathematik, 1959, 1:269–271, DOI:10.1007/BF01386390.',
 '[3] Brandes U, A Faster Algorithm for Betweenness Centrality, Journal of Mathematical Sociology, 2001, 25(2):163–177, DOI:10.1080/0022250X.2001.9990249.',
 '[4] NetworkX Developers, NetworkX 3.3 Reference: betweenness_centrality, 2024, https://networkx.org/documentation/networkx-3.3/reference/algorithms/generated/networkx.algorithms.centrality.betweenness_centrality.html（本机已安装版本函数文档）。']
for text in refs:
    p=para(text,size=10.5,indent=False);p.paragraph_format.line_spacing=1;p.paragraph_format.space_after=Pt(6)

page()
heading('附录A 核心路由源程序')
para('完整实现见src/NetworkController.cc。以下节选为每个存活源初始化后的最短距离计算，完整工程同时包含状态检查及下一跳回溯。',indent=False)
src=(ROOT/'project/src/NetworkController.cc').read_text('utf-8')
start=src.index('        for (int iter = 0; iter < numSats; ++iter)')
end=src.index('\n        for (int dst = 0;',start)
code(textwrap.dedent(src[start:end]))
para('对每个可达目的，从dst沿prev回溯至源的后继cur，再将gateByNeighbor[{src,cur}]写入sat[src]的下一跳表。失败节点和不可达目的不写项。',indent=False)

page()
heading('附录B 包统计与转发源程序')
para('NetworkController.cc：同批统计节选；包终止日志的完整写入实现见同一源文件。',indent=False)
start=src.index('void NetworkController::packetSent')
end=src.index('    if (trace.is_open())',start)
code(src[start:end]+'}')
para('Satellite.cc：成功接收时累加时延与跳数，并将终止事件交给控制器。无路由或到达失效节点也记录终止事件后删除包。',indent=False)
sat=(ROOT/'project/src/Satellite.cc').read_text('utf-8')
start=sat.index('    if (pkt->getDst() == nodeId)')
end=sat.index('\n    forwardPacket(pkt);',start)
snippet=textwrap.dedent(sat[start:end])
snippet=snippet.replace('check_and_cast<NetworkController *>(getParentModule()->getSubmodule("controller"))->packetEnded(pkt, "received");',
    'check_and_cast<NetworkController *>(\n        getParentModule()->getSubmodule("controller")\n    )->packetEnded(pkt, "received");')
code(snippet)

page()
heading('附录C 配置与复现入口')
para('在OMNeT++自带终端中，将project复制到ASCII路径后生成Makefile并编译。以下命令在工程根目录执行，Python需要能访问requirements.txt中的依赖；详细Windows启动方式见README。',indent=False)
code('opp_makemake -f --deep -o isl\nmake -j4\npython scripts/run_experiments.py --suite all \\\n  --output results/reproduce-new\npython scripts/verify_and_plot.py \\\n  --dir results/reproduce-new')
para('正式24节点参数节选：',indent=False)
code('network = IslNetwork\nsim-time-limit = 70s\n**.numSats = 24\n**.sendInterval = 1s\n**.startTime = 1s\n**.stopTime = 60s\n**.failureEnabled = true\n**.failureTime = 40s\n**.detectionDelay = 2s\n**.recoveryEnabled = true\n**.failureNodes = "8,12,1,5,19,23"')
para('本次正式数据位于results/final-20261105/。raw_summary.csv为66次基础及配对运行，sweep_summary.csv为440次逐次扫描，sweep_groups.csv为22组均值与SD，checks_summary.csv为1次边界检查，verification.json保存守恒核验及恢复路径证据。manifest.json记录仿真时源码和配置哈希。',indent=False)
para('终止包CSV保留每个实际发送包的去向；sca提供原始标量；log保存仿真运行过程。复现脚本拒绝覆盖已有输出，按配置和seed区分文件。完整src、simulations、scripts、configs及依赖清单随报告提交。',indent=False)

temp=ROOT/'文档工作/report-working.docx';d.save(temp)
# Preserve every opaque source package part byte-for-byte.
allowed={'word/document.xml','word/_rels/document.xml.rels','[Content_Types].xml'}
with ZipFile(REF) as z:base={n:z.read(n) for n in z.namelist()}
with ZipFile(temp) as z:new={n:z.read(n) for n in z.namelist()}
dest=OUT/'课程设计报告_成员A.docx'
with ZipFile(dest,'w',ZIP_DEFLATED) as z:
    for n,data in base.items():z.writestr(n,new[n] if n in allowed else data)
    for n,data in new.items():
        if n not in base:
            assert n.startswith('word/media/'),n
            z.writestr(n,data)
with ZipFile(dest) as z:
    assert all(z.read(n)==data for n,data in base.items() if n not in allowed)
print(dest)
