# 导航卫星星间通信网络抗毁性与通信性能仿真

OMNeT++ 6.4.0、24节点/40条双向链路、带传播时延权重的Dijkstra路由；比较随机失效、自适应介数定向攻击与路由更新开关。

## 已验证版本

2026-11-05在独立目录 `D:\work\isl-final-20261105` 从源码重新编译并运行 **507次**：66次基础/配对实验、440次扫描、1次非整数失效边界检查。数据位于 `results/final-20261105/`，旧 `raw/`、`sweep/` 及旧汇总保留供追溯。本报告以新版数据为准。

| 场景 | 次数 | 全时段PDR | 失效后同批PDR |
|---|---:|---:|---:|
| 基线 | 1 | 100% | — |
| 定向 k=6，更新开 | 20 | 74.1248% | 10.0529% |
| 定向 k=6，更新关 | 1 | 71.2329% | 0% |
| 随机 k=6，更新开 | 20 | 90.5403% | 67.1164% |
| 随机 k=6，更新关 | 20 | 75.0685% | 13.3333% |
| 仅S8失效，更新开 | 1 | 97.6744% | 93.1677% |
| 仅S8失效，更新关 | 1 | 89.6406% | 69.5652% |

随机行是20次均值，SD见CSV及verification.json。相同seed的随机开关恢复使用完全相同失效节点。507次运行逐包守恒、路径合法性、均值及同批计数核验通过。

## 环境

- Windows 11 x64；OMNeT++ 6.4.0 Windows包及其clang64工具链，按官方安装指南构建环境。
- Python 3.12；分析依赖见 `requirements.txt`，可用 `python -m pip install -r requirements.txt`。
- 仿真未依赖INET。图表中文字体使用Microsoft YaHei/SimHei。

## 从源码复现

将本工程复制到**不含中文和空格的新目录**。以下在当前课设目录的PowerShell中执行，目标必须不存在：

```powershell
Copy-Item -LiteralPath '.\project' -Destination 'D:\work\isl-reproduce' -Recurse
```

然后打开OMNeT++安装目录自带的终端，执行：

```bash
cd /d/work/isl-reproduce
opp_makemake -f --deep -o isl
make -j4
# 使用已安装分析依赖的Python，按本机路径修改。
/d/Users/19739/anaconda3/python.exe scripts/run_experiments.py \
  --suite all --output results/reproduce-new
/d/Users/19739/anaconda3/python.exe scripts/verify_and_plot.py \
  --dir results/reproduce-new
/d/Users/19739/anaconda3/python.exe scripts/analyze_sweep.py \
  --dir results/reproduce-new/sweep \
  --csv results/reproduce-new/sweep_groups.csv \
  --out results/reproduce-new/figures/sweep_pdr_lcc.png
/d/Users/19739/anaconda3/python.exe scripts/plot_results.py \
  --csv results/reproduce-new/raw_summary.csv \
  --out results/reproduce-new/figures/pdr_random_vs_targeted.png
/d/Users/19739/anaconda3/python.exe scripts/make_design_figures.py \
  --out results/reproduce-new/figures
```

等效的本机PowerShell非交互构建和批跑命令（已验证此方式）：

```powershell
& 'D:\omnetpp-6.4.0\tools\win32.x86_64\usr\bin\bash.exe' -lc 'export PATH=/clang64/bin:/d/omnetpp-6.4.0/bin:$PATH; cd /d/omnetpp-6.4.0; source setenv -f; cd /d/work/isl-reproduce; opp_makemake -f --deep -o isl && make -j4 && /d/Users/19739/anaconda3/python.exe scripts/run_experiments.py --suite all --output results/reproduce-new'
```

`--suite basic`运行66次；`sweep`运行440次；`checks`运行1次；`all`共507次。输出目录若存在即拒绝运行；再次复现请换新目录。每次配置与seed均生成独立sca、包CSV和log，避免覆盖正式数据。

## 结果与图表

```text
results/final-20261105/
  raw/                 # 66个基础及配对运行
  sweep/               # 440个扫描运行
  checks/              # 40.1s失效边界实验
  raw_summary.csv      # 基础逐次统计，含时延/跳数/吞吐/业务完成率
  sweep_summary.csv    # 扫描逐次统计
  sweep_groups.csv     # 22组均值与SD
  checks_summary.csv   # 边界检查
  verification.json    # 507次核验结果、统计均值/SD、恢复路径
  manifest.json        # 运行矩阵、仿真时源码和配置哈希
  figures/             # 设计图、性能图、路径/时间线
```

单独重新汇总时，将 `--results` 指向直接存放sca的目录，例如：

```bash
python scripts/analyze_results.py --results results/final-20261105/raw \
  --out results/new-summary.csv
```

不递归混合多个实验目录；无输入会报错。`generate_topology.py`重生成configs与src/IslNetwork.ned；`generate_batch_ini.py`据关键节点序列生成simulations/batch.ini，修改拓扑后需重新编译并重跑实验。

## 模型与指标

- 静态3×8抽象拓扑，同面环24边、相邻面同序号16边。编号不是实际卫星编号。
- `ned.DelayChannel`仅传播：同面70 ms、跨面120 ms；无带宽限制、队列和固定处理时延。
- 每节点向 `(id+12)%24`，1024 B/包，1包/s；1–60 s发包含60 s，仿真至70 s排空。
- 40 s失效，42 s更新；控制事件优先于同一时刻的发包事件。失效节点停发并丢弃到达包，NED连线仍可见。
- 定向攻击离线逐次重算无权介数，依次选择8、12、1、5、19、23；仿真中40 s同时失效。路由按传播时延加权，二者权重定义不同。
- 失效后PDR：发送/接收都按包`createdAt>=failureTime`分组。旧版截点指标只供历史核对。
- 平均时延、跳数只统计成功包。有效吞吐=接收×8192 bit/70 s，单位kbps；业务完成率=接收/1440，保留源停发造成的损失。
- `routeUpdateDelay`是配置等待2 s；单节点案例业务首包恢复间隔按日志另算，6条受影响且端点存活流为2.40–2.52 s。图为日志重绘，不冒充Qtenv截图。
- 失效后PDR和LCC是主要抗毁指标；全时段PDR还受失效源停发影响。大k时PDR回升不代表更安全。
- 无故障理论：16条流400 ms/5跳，8条流520 ms/6跳，故平均440 ms/5.333跳，匹配实测。

## 交互演示

见 `验收演示.md`。源码在 `src/`，配置在 `simulations/`，完整交付源码按本README可重编译。报告已填写成员A、成员B、成员C、成员D、成员E五人的姓名学号及指定分工，待成员核对反馈和实际完成日期定稿。当前以报告提交为主，演示说明作为工程附带资料。
