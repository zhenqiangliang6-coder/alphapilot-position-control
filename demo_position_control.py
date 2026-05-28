# -*- coding: utf-8 -*-
"""简易演示仓位控制功能"""

import sys
sys.path.insert(0, r'D:\mpython')

from utils.logger import init_logger
init_logger('logs')

from risk.position_control import PositionControl

print("=" * 70)
print("仓位控制模块 - 实时演示")
print("=" * 70)

# 1. 从HTML加载信号
pc = PositionControl(signal_file=r"D:\ESC\ESC\forecast_report.html")

print(f"\n📊 当前信号: {pc.position_signal}")
print(f"📊 仓位系数: {pc.position_ratio * 100:.0f}%")

# 2. 模拟仓位检查场景
total_asset = 3000000  # 假设总资产300万

print("\n" + "=" * 70)
print("仓位上限检查演示")
print("=" * 70)

scenarios = [
    (900000, "持仓90万(30%)"),
    (1500000, "持仓150万(50%)"),
    (600000, "持仓60万(20%)"),
]

for market_value, desc in scenarios:
    allowed, current_ratio, max_ratio = pc.check_buy_allowed(market_value, total_asset)
    
    status = "✅ 允许买入" if allowed else "❌ 拦截买入"
    print(f"\n{desc}: {status}")
    print(f"   当前仓位: {current_ratio*100:.1f}% | 上限: {max_ratio*100:.0f}%")

print("\n" + "=" * 70)
print("演示完成！")
print("=" * 70)
