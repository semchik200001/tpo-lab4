#!/usr/bin/env python3
"""Box-plot времени отклика по числу пользователей (нагрузочное тестирование).

Ось X — точное количество одновременных пользователей (потоков), для каждого
значения строится «ящик с усами» по времени отклика выбранной конфигурации.
Дополнительно нанесены среднее и медианное значения и порог 680 мс.
"""
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(BASE, 'load', 'result', 'results.csv')
OUT = os.path.join(BASE, 'boxplot_load.png')
THRESHOLD_MS = 680
CONFIG = 3  # выбранная конфигурация

df = pd.read_csv(CSV)
df['config'] = df['URL'].str.extract(r'config=(\d)').astype(int)
g = df[df['config'] == CONFIG]

levels = sorted(g['grpThreads'].unique())
data = [g[g['grpThreads'] == n]['elapsed'].values for n in levels]
means = [v.mean() for v in data]
medians = [np.median(v) for v in data]
counts = [len(v) for v in data]

from matplotlib.colors import LinearSegmentedColormap
plt.style.use('seaborn-v0_8-whitegrid')
fig, ax = plt.subplots(figsize=(13, 7))

# цвет ящиков по медиане: зелёный -> жёлтый -> красный
cmap = LinearSegmentedColormap.from_list('health', ['#2ecc71', '#f1c40f', '#e74c3c'])
mmin, mmax = min(medians), max(medians)
box_colors = [cmap((m - mmin) / (mmax - mmin + 1e-9)) for m in medians]

bp = ax.boxplot(data, positions=levels, widths=0.5, patch_artist=True,
                showfliers=True, flierprops=dict(marker='o', ms=3.5, alpha=0.25,
                markerfacecolor='#7f8c8d', markeredgecolor='none'),
                medianprops=dict(color='#1a1a1a', lw=2.8),
                whiskerprops=dict(color='#34495e', lw=1.6),
                capprops=dict(color='#34495e', lw=1.6),
                boxprops=dict(lw=1.4))
for box, c in zip(bp['boxes'], box_colors):
    box.set(facecolor=c, edgecolor='#2c3e50', alpha=0.92)

# среднее и медиана — крупные яркие маркеры с белой обводкой
ax.plot(levels, means, color='#2980b9', marker='D', ms=10, lw=2.4,
        markeredgecolor='white', markeredgewidth=1.3, label='Среднее', zorder=6)
ax.plot(levels, medians, color='#16a085', marker='s', ms=9, lw=2.4,
        markeredgecolor='white', markeredgewidth=1.3, label='Медиана', zorder=6)
ax.axhline(THRESHOLD_MS, color='#c0392b', ls='--', lw=2.4, label=f'Порог {THRESHOLD_MS} мс', zorder=4)
ax.axhspan(THRESHOLD_MS, ax.get_ylim()[1], color='#e74c3c', alpha=0.05, zorder=0)

# подписи: точное число замеров под каждой группой
y0 = ax.get_ylim()[0]
for n, c in zip(levels, counts):
    ax.annotate(f'n={c}', (n, y0), textcoords='offset points', xytext=(0, -24),
                ha='center', fontsize=8.5, color='#444')

ax.set_xlabel('Количество одновременных пользователей', labelpad=20, fontsize=12)
ax.set_ylabel('Время отклика, мс', fontsize=12)
ax.set_title(f'Распределение времени отклика по числу пользователей '
             f'(нагрузочный тест, config #{CONFIG})', fontsize=14, fontweight='bold')
ax.set_xticks(levels)
ax.grid(axis='y', alpha=0.3)
ax.legend(loc='upper left', fontsize=11, framealpha=0.95)
plt.tight_layout()
plt.savefig(OUT, dpi=150, bbox_inches='tight')
print('Среднее/медиана по числу пользователей:')
for n, mn, md, c in zip(levels, means, medians, counts):
    print(f'  {n} польз.: среднее={mn:.0f} медиана={md:.0f} (n={c})')
print(f'График сохранён: {OUT}')
