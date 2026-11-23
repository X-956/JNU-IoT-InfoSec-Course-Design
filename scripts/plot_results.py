# -*- coding: utf-8 -*-
"""Plot PDR and connectivity from the aggregated OMNeT++ summary CSV."""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    df = pd.read_csv(args.csv)
    df = df[df["failed"] == 6]
    random = df[df["config"] == "IslRandomFailure"]
    targeted = df[df["config"] == "IslFailure"]

    def ms(series):
        s = series.dropna()
        return s.mean(), s.std(ddof=1) if len(s) > 1 else 0.0

    labels = ["随机失效\n(random, k=6)", "定向攻击\n(adaptive betweenness, k=6)"]
    overall = [ms(random["pdr"])[0], ms(targeted["pdr"])[0]]
    overall_sd = [ms(random["pdr"])[1], ms(targeted["pdr"])[1]]
    after = [ms(random["pdr_after"])[0], ms(targeted["pdr_after"])[0]]
    after_sd = [ms(random["pdr_after"])[1], ms(targeted["pdr_after"])[1]]
    lcc = [ms(random["lcc"])[0], ms(targeted["lcc"])[0]]
    lcc_sd = [ms(random["lcc"])[1], ms(targeted["lcc"])[1]]

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.4), dpi=200)
    x = range(len(labels))
    w = 0.34
    ax = axes[0]
    ax.bar([i - w / 2 for i in x], overall, w, yerr=overall_sd, capsize=4,
           color="#2f6fb0", label="全时段 PDR")
    ax.bar([i + w / 2 for i in x], after, w, yerr=after_sd, capsize=4,
           color="#c62828", label="失效后 PDR")
    for i, (a, b) in enumerate(zip(overall, after)):
        ax.text(i - w / 2, a + 2, f"{a:.1f}%", ha="center", fontsize=9)
        ax.text(i + w / 2, b + 2, f"{b:.1f}%", ha="center", fontsize=9)
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 112)
    ax.set_ylabel("投递率 PDR (%)")
    ax.set_title("投递率：随机失效 vs 定向攻击")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(fontsize=8, loc="lower left")

    ax = axes[1]
    ax.bar(x, lcc, 0.5, yerr=lcc_sd, capsize=5,
           color=["#2f9e6f", "#c62828"])
    for i, v in enumerate(lcc):
        ax.text(i, v + 0.4, f"{v:.1f}", ha="center", fontsize=10)
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 25)
    ax.set_ylabel("最大连通分量节点数")
    ax.set_title("拓扑连通性（失效后）")
    ax.grid(axis="y", alpha=0.25)

    fig.suptitle("24 节点星间网络：k=6 失效，20 个随机种子，恢复开启\n"
                 "OMNeT++ 6.4.0 数据包级仿真", fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, bbox_inches="tight", facecolor="white")
    print(args.out)


if __name__ == "__main__":
    main()
