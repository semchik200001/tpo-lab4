#!/usr/bin/env python3
"""Зависимость времени отклика от числа пользователей (стресс-тестирование).

Строит линейный график среднего и медианного времени отклика выбранной
конфигурации в зависимости от количества одновременных пользователей (потоков).
Данные собраны через SSH-туннель, поэтому агрегируются по диапазонам нагрузки;
медиана устойчива к сетевым выбросам. Порог 680 мс показан пунктиром.
"""
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(BASE, 'stress', 'result', 'results.csv')
OUT = os.path.join(BASE, 'response_time_vs_load.png')
THRESHOLD_MS = 680
BIN = 10  # ширина диапазона нагрузки (пользователей) для агрегации

df = pd.read_csv(CSV)
df = df[df['grpThreads'] > 0].copy()
df['users'] = ((df['grpThreads'] - 1) // BIN) * BIN + BIN // 2  # центр диапазона

agg = df.groupby('users')['elapsed'].agg(
    mean='mean', median='median', n='count').reset_index()
agg = agg[agg['n'] >= 5]

plt.style.use('seaborn-v0_8-whitegrid')
fig, ax = plt.subplots(figsize=(13, 6.5))

ax.fill_between(agg['users'], THRESHOLD_MS, agg['mean'],
                where=(agg['mean'] > THRESHOLD_MS), color='#e74c3c', alpha=0.10, zorder=0)
ax.plot(agg['users'], agg['mean'], color='#2980b9', marker='D', ms=7, lw=2.8,
        markeredgecolor='white', markeredgewidth=1.1, label='Среднее', zorder=5)
ax.plot(agg['users'], agg['median'], color='#16a085', marker='s', ms=7, lw=2.8,
        markeredgecolor='white', markeredgewidth=1.1, label='Медиана', zorder=5)
ax.axhline(THRESHOLD_MS, color='#c0392b', ls='--', lw=2.4, label=f'Порог {THRESHOLD_MS} мс', zorder=4)

ax.set_xlabel('Количество одновременных пользователей', fontsize=12)
ax.set_ylabel('Время отклика, мс', fontsize=12)
ax.set_title('Зависимость времени отклика от числа пользователей '
             '(стресс-тест, config #3)', fontsize=14, fontweight='bold')
ax.legend(loc='upper left', fontsize=11, framealpha=0.95)
ax.grid(alpha=0.3)
ax.set_xlim(0, agg['users'].max() + 5)
plt.tight_layout()
plt.savefig(OUT, dpi=150, bbox_inches='tight')

print('Среднее/медиана по числу пользователей:')
print(agg.to_string(index=False))
over = agg[agg['median'] > THRESHOLD_MS]
ok = agg[agg['median'] <= THRESHOLD_MS]
print("\nИТОГ (по медиане):")
if not over.empty:
    print(f"  Порог {THRESHOLD_MS} мс по медиане превышается с ~{int(over.iloc[0]['users'])} пользователей")
    if not ok.empty:
        print(f"  Макс. нагрузка с медианой в пределах порога: ~{int(ok['users'].max())} пользователей")
else:
    print(f"  Медиана не превышает {THRESHOLD_MS} мс на всём диапазоне")
print(f"График сохранён: {OUT}")
