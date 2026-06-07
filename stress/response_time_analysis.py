#!/usr/bin/env python3
"""Анализ стресс-тестирования: график зависимости времени отклика от нагрузки.

Результаты собраны через SSH-туннель до сервера кафедры, поэтому в сырых данных
присутствуют сетевые выбросы. Для построения наглядной зависимости данные
агрегируются по диапазонам нагрузки (бинам) с использованием медианы и
перцентилей, устойчивых к выбросам.
"""
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(BASE, 'stress', 'result', 'results.csv')
OUT = os.path.join(BASE, 'response_time_vs_load.png')
THRESHOLD_MS = 680
BIN = 10  # ширина диапазона нагрузки (потоков) для агрегации

df = pd.read_csv(CSV)
df = df[df['grpThreads'] > 0].copy()
df['bin'] = ((df['grpThreads'] - 1) // BIN) * BIN + BIN // 2  # центр диапазона

agg = df.groupby('bin')['elapsed'].agg(
    median='median',
    mean='mean',
    p90=lambda s: s.quantile(0.9),
    p95=lambda s: s.quantile(0.95),
    p99=lambda s: s.quantile(0.99),
    n='count',
).reset_index()
agg = agg[agg['n'] >= 5]  # отбрасываем диапазоны с недостатком данных

print("Агрегированная статистика по диапазонам нагрузки:")
print(agg.to_string(index=False))
print("\n" + "=" * 80)

plt.style.use('seaborn-v0_8-whitegrid')
fig, axes = plt.subplots(1, 2, figsize=(15, 5.5))
fig.suptitle('Зависимость времени отклика от нагрузки (стресс-тестирование, config #3)',
             fontsize=14, fontweight='bold')

# --- Левый график: медиана и среднее ---
ax1 = axes[0]
ax1.plot(agg['bin'], agg['median'], color='#2ca02c', marker='s', ms=4, lw=2, label='Медиана')
ax1.plot(agg['bin'], agg['mean'], color='#1f77b4', marker='o', ms=4, lw=2, label='Среднее')
ax1.axhline(THRESHOLD_MS, color='#d62728', ls='--', lw=2, label=f'Порог ({THRESHOLD_MS} мс)')
ax1.fill_between(agg['bin'], THRESHOLD_MS, agg['median'],
                 where=(agg['median'] > THRESHOLD_MS), color='#d62728', alpha=0.12)
ax1.set_xlabel('Нагрузка (количество параллельных потоков)')
ax1.set_ylabel('Время отклика, мс')
ax1.set_title('Медианное и среднее время отклика')
ax1.legend(loc='upper left')

# --- Правый график: перцентили ---
ax2 = axes[1]
ax2.plot(agg['bin'], agg['p90'], color='#1f77b4', marker='o', ms=4, lw=2, label='P90')
ax2.plot(agg['bin'], agg['p95'], color='#ff7f0e', marker='s', ms=4, lw=2, label='P95')
ax2.plot(agg['bin'], agg['p99'], color='#9467bd', marker='^', ms=4, lw=2, label='P99')
ax2.axhline(THRESHOLD_MS, color='#d62728', ls='--', lw=2, label=f'Порог ({THRESHOLD_MS} мс)')
ax2.set_xlabel('Нагрузка (количество параллельных потоков)')
ax2.set_ylabel('Время отклика, мс')
ax2.set_title('Перцентили времени отклика')
ax2.legend(loc='upper left')

plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.savefig(OUT, dpi=150, bbox_inches='tight')
print(f"График сохранён: {OUT}")

# --- Точка пробоя порога по медиане ---
print("\nИТОГОВЫЙ АНАЛИЗ (по медиане, устойчивой к сетевым выбросам):")
over = agg[agg['median'] > THRESHOLD_MS]
ok = agg[agg['median'] <= THRESHOLD_MS]
if not over.empty:
    first = int(over.iloc[0]['bin'])
    max_ok = int(ok['bin'].max()) if not ok.empty else 0
    print(f"  Порог {THRESHOLD_MS} мс по медиане превышается начиная с диапазона ~{first} потоков")
    print(f"  Максимальная нагрузка с медианой в пределах порога: ~{max_ok} потоков")
else:
    print(f"  Медиана не превышает {THRESHOLD_MS} мс на всём диапазоне нагрузки")
