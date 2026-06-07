#!/usr/bin/env python3
"""Графики и таблица по результатам нагрузочного тестирования трёх конфигураций.

Генерирует три изображения для отчёта:
  load_stats_table.png   — итоговая таблица статистики (аналог JMeter Statistics);
  load_over_time.png     — среднее время отклика по ходу теста для каждой конфигурации;
  config_comparison.png  — сравнение конфигураций (время отклика, % превышений, throughput).
"""
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(BASE, 'load', 'result', 'results.csv')
THRESHOLD_MS = 680
PRICES = {1: 5500, 2: 8800, 3: 11100}

df = pd.read_csv(CSV)
df['config'] = df['URL'].str.extract(r'config=(\d)').astype(int)
plt.style.use('seaborn-v0_8-whitegrid')

# ------- собираем статистику -------
rows = []
for cfg in sorted(df['config'].unique()):
    g = df[df['config'] == cfg]
    s = g['elapsed']
    dur_s = (g['timeStamp'].max() - g['timeStamp'].min()) / 1000
    rows.append(dict(config=cfg, price=PRICES[cfg], n=len(s),
                     mean=s.mean(), median=s.median(),
                     p90=s.quantile(.9), p95=s.quantile(.95), p99=s.quantile(.99),
                     mn=s.min(), mx=s.max(),
                     over=(s > THRESHOLD_MS).mean() * 100,
                     tps=len(s) / dur_s if dur_s else 0))
stats = pd.DataFrame(rows)
print(stats.to_string(index=False))

# ================= 1) ТАБЛИЦА СТАТИСТИКИ =================
fig, ax = plt.subplots(figsize=(13, 2.6))
ax.axis('off')
ax.set_title('Статистика нагрузочного тестирования (7 пользователей, порог 680 мс)',
             fontsize=13, fontweight='bold', pad=14)
cols = ['Конфигурация', 'Цена, $', 'Запросов', 'Среднее, мс', 'Медиана, мс',
        'P90, мс', 'P95, мс', 'P99, мс', 'Min, мс', 'Max, мс', '> 680 мс, %']
cell, colors = [], []
for _, r in stats.iterrows():
    cell.append([f"#{int(r['config'])} request", f"{int(r['price'])}", f"{int(r['n'])}",
                 f"{r['mean']:.0f}", f"{r['median']:.0f}", f"{r['p90']:.0f}",
                 f"{r['p95']:.0f}", f"{r['p99']:.0f}", f"{int(r['mn'])}",
                 f"{int(r['mx'])}", f"{r['over']:.1f}"])
    # подсветка строки конфига №3 (выбранной)
    base = '#e8f5e9' if int(r['config']) == 3 else '#fdecea' if r['over'] >= 99.9 else '#fff8e1'
    colors.append([base] * len(cols))
t = ax.table(cellText=cell, colLabels=cols, loc='center', cellLoc='center', cellColours=colors)
t.auto_set_font_size(False); t.set_fontsize(10); t.scale(1, 1.6)
for j in range(len(cols)):
    c = t[0, j]; c.set_facecolor('#4472C4'); c.set_text_props(color='white', fontweight='bold')
plt.tight_layout()
plt.savefig(os.path.join(BASE, 'load_stats_table.png'), dpi=150, bbox_inches='tight')
plt.close()

# ================= 2) ВРЕМЯ ОТКЛИКА ПО ХОДУ ТЕСТА =================
fig, ax = plt.subplots(figsize=(13, 5.5))
colmap = {1: '#d62728', 2: '#1f77b4', 3: '#2ca02c'}
for cfg in sorted(df['config'].unique()):
    g = df[df['config'] == cfg].copy().sort_values('timeStamp')
    t0 = g['timeStamp'].min()
    g['sec'] = (g['timeStamp'] - t0) / 1000
    # сглаживание скользящим средним по 15 запросам
    g['smooth'] = g['elapsed'].rolling(15, min_periods=1).mean()
    ax.plot(g['sec'], g['smooth'], color=colmap[cfg], lw=2,
            label=f'Config #{cfg} (${PRICES[cfg]})')
ax.axhline(THRESHOLD_MS, color='#d62728', ls='--', lw=2, label=f'Порог {THRESHOLD_MS} мс')
ax.set_xlabel('Время от начала прогона конфигурации, с')
ax.set_ylabel('Время отклика (скользящее среднее), мс')
ax.set_title('Время отклика по ходу нагрузочного теста (7 пользователей)',
             fontsize=13, fontweight='bold')
ax.legend(loc='upper right')
plt.tight_layout()
plt.savefig(os.path.join(BASE, 'load_over_time.png'), dpi=150, bbox_inches='tight')
plt.close()

# ================= 3) СРАВНЕНИЕ КОНФИГУРАЦИЙ =================
fig, axes = plt.subplots(1, 3, figsize=(18, 5.5))
fig.suptitle('Сравнение конфигураций по результатам нагрузочного тестирования (7 пользователей)',
             fontsize=14, fontweight='bold')
labels = [f'#{int(c)}\n(${PRICES[int(c)]})' for c in stats['config']]
x = np.arange(len(stats)); bar_colors = ['#d62728', '#ff7f0e', '#2ca02c']

ax = axes[0]; w = 0.2
ax.bar(x - 1.5*w, stats['mean'], w, label='Среднее', color='#1f77b4')
ax.bar(x - 0.5*w, stats['median'], w, label='Медиана', color='#2ca02c')
ax.bar(x + 0.5*w, stats['p95'], w, label='P95', color='#ff7f0e')
ax.bar(x + 1.5*w, stats['p99'], w, label='P99', color='#9467bd')
ax.axhline(THRESHOLD_MS, color='#d62728', ls='--', lw=2, label=f'Порог {THRESHOLD_MS} мс')
ax.set_xticks(x); ax.set_xticklabels(labels); ax.set_ylabel('Время отклика, мс')
ax.set_title('Время отклика по конфигурациям'); ax.legend(fontsize=8)

ax = axes[1]
b = ax.bar(x, stats['over'], color=bar_colors, width=0.5)
ax.set_xticks(x); ax.set_xticklabels(labels); ax.set_ylabel('% запросов выше порога')
ax.set_title(f'Доля запросов > {THRESHOLD_MS} мс'); ax.set_ylim(0, 105)
for bi, v in zip(b, stats['over']):
    ax.text(bi.get_x()+bi.get_width()/2, v+1, f'{v:.1f}%', ha='center', fontsize=9)

ax = axes[2]
b = ax.bar(x, stats['tps'], color='#1f77b4', width=0.5)
ax.set_xticks(x); ax.set_xticklabels(labels); ax.set_ylabel('Запросов/сек')
ax.set_title('Пропускная способность')
for bi, v in zip(b, stats['tps']):
    ax.text(bi.get_x()+bi.get_width()/2, v+0.03, f'{v:.2f}', ha='center', fontsize=9)

plt.tight_layout(rect=[0, 0, 1, 0.95])
plt.savefig(os.path.join(BASE, 'config_comparison.png'), dpi=150, bbox_inches='tight')
plt.close()
print('Графики сохранены: load_stats_table.png, load_over_time.png, config_comparison.png')
