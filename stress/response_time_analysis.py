import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

df = pd.read_csv('/Users/admin/tpo-4/stress/result/results.csv')

stats = df.groupby('grpThreads')['elapsed'].agg([
    'mean',
    'median',
    'min',
    'max',
    'std'
]).reset_index()

percentiles = df.groupby('grpThreads')['elapsed'].quantile([0.9, 0.95, 0.99]).unstack()
percentiles.columns = ['p90', 'p95', 'p99']
stats = stats.merge(percentiles, left_on='grpThreads', right_index=True)

THRESHOLD_MS = 740

print("Статистика по нагрузке:")
print(stats.to_string(index=False))
print("\n" + "="*80 + "\n")

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle('Анализ времени отклика в зависимости от нагрузки', fontsize=14, fontweight='bold')

ax1 = axes[0]
ax1.plot(stats['grpThreads'], stats['mean'], 'b-o', label='Среднее', linewidth=2, markersize=6)
ax1.plot(stats['grpThreads'], stats['median'], 'g-s', label='Медиана', linewidth=2, markersize=6)
ax1.axhline(y=THRESHOLD_MS, color='r', linestyle='--', linewidth=2, label=f'Порог ({THRESHOLD_MS} мс)')
ax1.fill_between(stats['grpThreads'], THRESHOLD_MS, stats['mean'], 
                  where=(stats['mean'] > THRESHOLD_MS), color='red', alpha=0.3)
ax1.set_xlabel('Нагрузка (количество потоков)', fontsize=10)
ax1.set_ylabel('Время отклика (мс)', fontsize=10)
ax1.set_title('Среднее и медианное время отклика')
ax1.legend()
ax1.grid(True, alpha=0.3)

threshold_exceeded = stats[stats['mean'] > THRESHOLD_MS]
if not threshold_exceeded.empty:
    max_load_before_threshold = stats[stats['mean'] <= THRESHOLD_MS]['grpThreads'].max() if len(stats[stats['mean'] <= THRESHOLD_MS]) > 0 else 0
    print(f"Порог {THRESHOLD_MS} мс превышен при нагрузке: {threshold_exceeded.iloc[0]['grpThreads']} потоков")
    print(f"Максимальная нагрузка без превышения порога: {max_load_before_threshold} потоков")
    print(f"Максимальная пропускная способность: ~{threshold_exceeded.iloc[0]['grpThreads'] * 1000 / THRESHOLD_MS:.1f} запросов/сек")
else:
    print(f"При всех нагрузках среднее время отклика не превышает {THRESHOLD_MS} мс")

ax2 = axes[1]
ax2.plot(stats['grpThreads'], stats['p90'], 'b-o', label='P90 (90% запросов)', linewidth=2, markersize=6)
ax2.plot(stats['grpThreads'], stats['p95'], 'g-s', label='P95 (95% запросов)', linewidth=2, markersize=6)
ax2.plot(stats['grpThreads'], stats['p99'], 'm-^', label='P99 (99% запросов)', linewidth=2, markersize=6)
ax2.axhline(y=THRESHOLD_MS, color='r', linestyle='--', linewidth=2, label=f'Порог ({THRESHOLD_MS} мс)')
ax2.set_xlabel('Нагрузка (количество потоков)', fontsize=10)
ax2.set_ylabel('Время отклика (мс)', fontsize=10)
ax2.set_title('Процентили времени отклика')
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('response_time_vs_load.png', dpi=150, bbox_inches='tight')
plt.show()

print("\n" + "="*80)
print("ИТОГОВЫЙ АНАЛИЗ:")
print("="*80)

for idx, row in stats.iterrows():
    if row['mean'] > THRESHOLD_MS:
        print(f"\nКРИТИЧЕСКАЯ НАГРУЗКА: {int(row['grpThreads'])} потоков")
        print(f"   - Среднее время отклика: {row['mean']:.1f} мс (превышает порог {THRESHOLD_MS} мс)")
        print(f"   - Медиана: {row['median']:.1f} мс")
        print(f"   - P99: {row['p99']:.1f} мс")
        print(f"   - Разброс: {row['min']:.0f} - {row['max']:.0f} мс")
        break
else:
    print(f"\nПри всех протестированных нагрузках (до {int(stats['grpThreads'].max())} потоков)")
    print(f"   среднее время отклика не превышает {THRESHOLD_MS} мс")
    print(f"   Максимальное среднее: {stats['mean'].max():.1f} мс при {int(stats.loc[stats['mean'].idxmax(), 'grpThreads'])} потоках")