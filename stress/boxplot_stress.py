#!/usr/bin/env python3
"""Box-plot времени отклика по диапазонам нагрузки (стресс-тестирование).

Ось X — диапазоны количества одновременных пользователей. Для каждого диапазона —
яркий «ящик с усами» по времени отклика. Цвет ящика отражает «здоровье» системы
(зелёный → жёлтый → красный по мере роста времени отклика). Логарифмическая шкала
по Y делает читаемыми и малые, и большие значения. Нанесены среднее, медиана,
порог 680 мс; зона выше порога подсвечена.
"""
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(BASE, 'stress', 'result', 'results.csv')
OUT = os.path.join(BASE, 'boxplot_stress.png')
THRESHOLD_MS = 680
BIN = 25

df = pd.read_csv(CSV)
df = df[df['grpThreads'] > 0].copy()
maxn = int(df['grpThreads'].max())
edges = list(range(0, maxn + BIN, BIN))

data, labels, means, medians, counts = [], [], [], [], []
for i in range(len(edges) - 1):
    lo, hi = edges[i], edges[i + 1]
    sub = df[(df['grpThreads'] > lo) & (df['grpThreads'] <= hi)]['elapsed'].values
    if len(sub) < 5:
        continue
    data.append(sub)
    labels.append(f'{lo + 1}–{hi}')
    means.append(sub.mean())
    medians.append(np.median(sub))
    counts.append(len(sub))

plt.style.use('seaborn-v0_8-whitegrid')
fig, ax = plt.subplots(figsize=(15, 7.5))
pos = np.arange(len(data))

# цвет ящика по медиане: зелёный (быстро) -> жёлтый -> красный (медленно)
cmap = LinearSegmentedColormap.from_list('health', ['#2ecc71', '#f1c40f', '#e74c3c'])
mmin, mmax = min(medians), max(medians)
box_colors = [cmap((m - mmin) / (mmax - mmin + 1e-9)) for m in medians]

bp = ax.boxplot(data, positions=pos, widths=0.62, patch_artist=True,
                showfliers=True,
                flierprops=dict(marker='o', ms=2.5, alpha=0.18,
                                markerfacecolor='#7f8c8d', markeredgecolor='none'),
                medianprops=dict(color='#1a1a1a', lw=2.8),
                whiskerprops=dict(color='#34495e', lw=1.6),
                capprops=dict(color='#34495e', lw=1.6),
                boxprops=dict(lw=1.4))
for box, c in zip(bp['boxes'], box_colors):
    box.set(facecolor=c, edgecolor='#2c3e50', alpha=0.92)

# среднее — крупные яркие ромбы с линией
ax.plot(pos, means, color='#2980b9', marker='D', ms=9, lw=2.4,
        markeredgecolor='white', markeredgewidth=1.2, label='Среднее', zorder=6)
# медиана — линия-связка по верхам медиан
ax.plot(pos, medians, color='#16a085', marker='s', ms=8, lw=2.4,
        markeredgecolor='white', markeredgewidth=1.2, label='Медиана', zorder=6)

# порог и подсветка зоны превышения
ax.axhline(THRESHOLD_MS, color='#c0392b', ls='--', lw=2.4, label=f'Порог {THRESHOLD_MS} мс', zorder=4)
ax.axhspan(THRESHOLD_MS, ax.get_ylim()[1], color='#e74c3c', alpha=0.05, zorder=0)

ax.set_yscale('log')
ax.set_ylim(bottom=max(300, df['elapsed'].min() * 0.9))
ax.set_xlabel('Количество одновременных пользователей (диапазон)', labelpad=20, fontsize=12)
ax.set_ylabel('Время отклика, мс (лог. шкала)', fontsize=12)
ax.set_title('Распределение времени отклика по нагрузке (стресс-тест, config #3)',
             fontsize=14, fontweight='bold')
ax.set_xticks(pos)
ax.set_xticklabels(labels, rotation=40, ha='right', fontsize=10)
ax.grid(axis='y', which='both', alpha=0.3)

# число замеров над осью X
ymin = ax.get_ylim()[0]
for p, c in zip(pos, counts):
    ax.annotate(f'n={c}', (p, ymin), textcoords='offset points', xytext=(0, -34),
                ha='center', fontsize=8, color='#555')

ax.legend(loc='upper left', fontsize=11, framealpha=0.95)
plt.tight_layout()
plt.savefig(OUT, dpi=150, bbox_inches='tight')
print('Среднее/медиана по диапазонам нагрузки:')
for lab, mn, md, c in zip(labels, means, medians, counts):
    print(f'  {lab} польз.: среднее={mn:.0f} медиана={md:.0f} (n={c})')
print(f'График сохранён: {OUT}')
