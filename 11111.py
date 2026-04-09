# -*- coding: utf-8 -*-
"""
聆达股份论文图表绘制脚本
生成：
1. 图2 其他应收款与预付账款变动趋势图
2. 图3 流动比率与速动比率变动趋势图
3. 图4 营业总收入、营业总成本与成本收入比变动趋势图

运行方法：
python plot_lingda_figures.py
"""

from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np


# =========================
# 1. 中文字体设置
# =========================
def get_chinese_font():
    """
    优先找宋体/衬线类中文字体。
    你如果想最稳，建议直接把下面第一个路径改成你自己电脑里的宋体路径。
    Windows 常见：
    C:/Windows/Fonts/simsun.ttc
    C:/Windows/Fonts/msyh.ttc
    """

    candidate_paths = [
        # Windows
        r"C:/Windows/Fonts/simsun.ttc",   # 宋体

    ]

    for fp in candidate_paths:
        if Path(fp).exists():
            return font_manager.FontProperties(fname=fp)

    # 如果找不到字体文件，就退回到字体名
    fallback_names = [
        "SimSun", "Songti SC", "STSong", "Microsoft YaHei",
        "SimHei", "Noto Serif CJK SC", "Noto Sans CJK SC"
    ]
    for name in fallback_names:
        try:
            prop = font_manager.FontProperties(family=name)
            return prop
        except Exception:
            continue

    return None


ZH_FONT = get_chinese_font()

plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 120


# =========================
# 2. 数据
# =========================
years = ["2020", "2021", "2022", "2023", "2024"]
x = np.arange(len(years))

# 图2：金额单位=万元
other_receivables = [4685, 4196, 852.5, 2682, 444.7]
prepayments = [4356, 11050, 2123, 3386, 1040]

# 图3：单位=%
current_ratio = [73.16, 89.60, 84.55, 70.95, 18.28]
quick_ratio = [69.41, 84.15, 77.10, 66.33, 16.97]

# 图4：收入/成本单位=亿元；成本收入比单位=%
revenue = [2.823, 10.80, 15.98, 8.389, 0.6115]
cost = [2.876, 11.92, 15.73, 8.912, 2.520]
cost_income_ratio = [101.88, 110.37, 98.44, 106.23, 412.10]


# =========================
# 3. 统一样式函数
# =========================
def apply_font_to_axis(ax, font_prop):
    """给坐标轴文字统一设置中文字体"""
    if font_prop is None:
        return

    # 坐标轴标签
    ax.xaxis.label.set_fontproperties(font_prop)
    ax.yaxis.label.set_fontproperties(font_prop)

    # 刻度标签
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontproperties(font_prop)


def style_axis(ax, font_prop):
    """统一论文风格"""
    ax.grid(True, linestyle="--", linewidth=0.6, alpha=0.35)
    for spine in ax.spines.values():
        spine.set_linewidth(1.0)
    apply_font_to_axis(ax, font_prop)


def save_figure(fig, out_png, out_pdf):
    """同时保存 PNG 和 PDF"""
    fig.savefig(out_png, dpi=400, bbox_inches="tight")
    fig.savefig(out_pdf, bbox_inches="tight")
    plt.close(fig)


# =========================
# 4. 输出目录
# =========================
out_dir = Path("C:\\Users\\user\\Desktop\\接单\\接单16")
out_dir.mkdir(exist_ok=True)


# =========================
# 5. 图2
# =========================
fig, ax = plt.subplots(figsize=(7.2, 4.6))

line1, = ax.plot(
    x, other_receivables,
    marker="o", linewidth=1.8, markersize=6,
    label="其他应收款"
)
line2, = ax.plot(
    x, prepayments,
    marker="s", linewidth=1.8, markersize=6,
    label="预付账款"
)

ax.set_xticks(x)
ax.set_xticklabels(years)
ax.set_xlabel("年份", fontproperties=ZH_FONT)
ax.set_ylabel("金额（万元）", fontproperties=ZH_FONT)

style_axis(ax, ZH_FONT)

legend = ax.legend(frameon=True, edgecolor="0.7", fontsize=10)
if ZH_FONT is not None:
    for t in legend.get_texts():
        t.set_fontproperties(ZH_FONT)

save_figure(
    fig,
    out_dir / "图2_其他应收款与预付账款变动趋势图.png",
    out_dir / "图2_其他应收款与预付账款变动趋势图.pdf"
)


# =========================
# 6. 图3
# =========================
fig, ax = plt.subplots(figsize=(7.2, 4.6))

line1, = ax.plot(
    x, current_ratio,
    marker="o", linewidth=1.8, markersize=6,
    label="流动比率"
)
line2, = ax.plot(
    x, quick_ratio,
    marker="s", linewidth=1.8, markersize=6,
    label="速动比率"
)

ax.set_xticks(x)
ax.set_xticklabels(years)
ax.set_xlabel("年份", fontproperties=ZH_FONT)
ax.set_ylabel("比率（%）", fontproperties=ZH_FONT)

style_axis(ax, ZH_FONT)

legend = ax.legend(frameon=True, edgecolor="0.7", fontsize=10)
if ZH_FONT is not None:
    for t in legend.get_texts():
        t.set_fontproperties(ZH_FONT)

save_figure(
    fig,
    out_dir / "图3_流动比率与速动比率变动趋势图.png",
    out_dir / "图3_流动比率与速动比率变动趋势图.pdf"
)


# =========================
# 7. 图4（双坐标轴）
# =========================
fig, ax1 = plt.subplots(figsize=(7.4, 4.8))

l1, = ax1.plot(
    x, revenue,
    marker="o", linewidth=1.8, markersize=6,
    label="营业总收入"
)
l2, = ax1.plot(
    x, cost,
    marker="s", linewidth=1.8, markersize=6,
    label="营业总成本"
)

ax1.set_xticks(x)
ax1.set_xticklabels(years)
ax1.set_xlabel("年份", fontproperties=ZH_FONT)
ax1.set_ylabel("金额（亿元）", fontproperties=ZH_FONT)

style_axis(ax1, ZH_FONT)

ax2 = ax1.twinx()
l3, = ax2.plot(
    x, cost_income_ratio,
    marker="^", linewidth=1.8, markersize=6,
    label="成本收入比"
)
ax2.set_ylabel("成本收入比（%）", fontproperties=ZH_FONT)

# 右侧纵轴字体
if ZH_FONT is not None:
    ax2.yaxis.label.set_fontproperties(ZH_FONT)
    for label in ax2.get_yticklabels():
        label.set_fontproperties(ZH_FONT)

for spine in ax2.spines.values():
    spine.set_linewidth(1.0)

# 合并图例
lines = [l1, l2, l3]
labels = [line.get_label() for line in lines]
legend = ax1.legend(lines, labels, loc="upper left", frameon=True, edgecolor="0.7", fontsize=10)
if ZH_FONT is not None:
    for t in legend.get_texts():
        t.set_fontproperties(ZH_FONT)

save_figure(
    fig,
    out_dir / "图4_营业总收入营业总成本与成本收入比变动趋势图.png",
    out_dir / "图4_营业总收入营业总成本与成本收入比变动趋势图.pdf"
)


print("图表已生成，保存在：", out_dir.resolve())
print("请在论文中单独添加图题，不要把长标题写进图里。")