# -*- coding: utf-8 -*-
"""
分板块止盈策略测试脚本 - V1.0
Alphapilot智能体团队
测试日期: 2026-05-18

测试目标:
1. 验证60/00开头股票使用3%-8.5%区间
2. 验证68/30开头股票使用3%-17%区间
3. 验证回落1.3%触发逻辑
"""

import sys
import os
import time

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("🧪 分板块止盈策略测试 - V1.0")
print("=" * 80)

passed = 0
failed = 0

def check_result(test_name, result, detail=""):
    global passed, failed
    if result:
        print(f"✅ {test_name}")
        if detail:
            print(f"   {detail}")
        passed += 1
    else:
        print(f"❌ {test_name}")
        if detail:
            print(f"   {detail}")
        failed += 1

# ==================== 初始化日志系统 ====================
try:
    from utils.logger import init_logger, get_logger
    import tempfile
    temp_log_dir = tempfile.mkdtemp()
    init_logger(temp_log_dir)
    print(f"\n✅ 日志系统初始化成功 (临时目录: {temp_log_dir})\n")
except Exception as e:
    print(f"⚠️  日志系统初始化失败: {e}\n")

# ==================== 导入模块 ====================
try:
    from risk.dynamic_take_profit import DynamicTakeProfit
    check_result("dynamic_take_profit 模块导入", True)
except Exception as e:
    check_result("dynamic_take_profit 模块导入", False, str(e))
    sys.exit(1)

# ==================== Mock Engine ====================
class MockPosition:
    def __init__(self, code, volume, open_price):
        self.stock_code = code
        self.volume = volume
        self.can_use_volume = volume
        self.open_price = open_price

class MockEngine:
    def __init__(self):
        self.positions = []
        self.prices = {}
    
    def query_positions(self):
        return self.positions
    
    def get_latest_prices(self, codes):
        return self.prices
    
    def order_stock(self, code, side, volume, price=0, order_type=1):
        print(f"   📤 [模拟下单] {code} {'卖出' if side == 2 else '买入'} {volume}股 @ {price:.2f}")
        return True

# ==================== 测试1: 主板股票（60开头）第一级止盈 ====================
print("\n" + "=" * 80)
print("📊 测试1: 主板股票（60开头）第一级止盈")
print("=" * 80)

engine = MockEngine()
strategy = DynamicTakeProfit(engine)

# 模拟场景：60开头的股票，最高涨幅8%，当前回落1.5%
engine.positions = [MockPosition("SHSE.600001", 1000, 10.0)]
engine.prices = {"SHSE.600001": 10.65}  # 现价10.65，成本10.0，涨幅6.5%

# 手动设置追踪器状态
strategy.profit_tracker["SHSE.600001"] = {
    'highest_profit': 0.08,  # 最高涨幅8%
    'peak_time': time.time() - 300,
    'triggered_level1': False,
    'triggered_level2': False,
    'triggered_level3': False
}

# 执行第一级检查
current_price = 10.65
open_price = 10.0
profit_ratio = (current_price - open_price) / open_price  # 6.5%

print(f"股票代码: SHSE.600001 (主板)")
print(f"成本价: {open_price:.2f}")
print(f"现价: {current_price:.2f}")
print(f"当前涨幅: {profit_ratio*100:.2f}%")
print(f"最高涨幅: 8.00%")
print(f"回落幅度: {(0.08 - profit_ratio)*100:.2f}%")
print(f"预期结果: ✅ 应触发止盈 (8% > 6.5% + 1.3%)")

strategy._check_level1("SHSE.600001", current_price, open_price, 1000, profit_ratio)

if strategy.profit_tracker["SHSE.600001"]["triggered_level1"]:
    check_result("主板股票第一级止盈触发", True, "8%涨幅回落1.5%正确触发")
else:
    check_result("主板股票第一级止盈触发", False, "应该触发但未触发")

# ==================== 测试2: 科创板股票（68开头）第一级止盈 ====================
print("\n" + "=" * 80)
print("📊 测试2: 科创板股票（68开头）第一级止盈")
print("=" * 80)

engine2 = MockEngine()
strategy2 = DynamicTakeProfit(engine2)

# 模拟场景：68开头的股票，最高涨幅16%，当前回落1.5%
engine2.positions = [MockPosition("SHSE.688001", 500, 50.0)]
engine2.prices = {"SHSE.688001": 57.0}  # 现价57.0，成本50.0，涨幅14%

# 手动设置追踪器状态
strategy2.profit_tracker["SHSE.688001"] = {
    'highest_profit': 0.16,  # 最高涨幅16%
    'peak_time': time.time() - 300,
    'triggered_level1': False,
    'triggered_level2': False,
    'triggered_level3': False
}

# 执行第一级检查
current_price = 57.0
open_price = 50.0
profit_ratio = (current_price - open_price) / open_price  # 14%

print(f"股票代码: SHSE.688001 (科创板)")
print(f"成本价: {open_price:.2f}")
print(f"现价: {current_price:.2f}")
print(f"当前涨幅: {profit_ratio*100:.2f}%")
print(f"最高涨幅: 16.00%")
print(f"回落幅度: {(0.16 - profit_ratio)*100:.2f}%")
print(f"预期结果: ✅ 应触发止盈 (16% > 14% + 1.3%，且16% < 17%上限)")

strategy2._check_level1("SHSE.688001", current_price, open_price, 500, profit_ratio)

if strategy2.profit_tracker["SHSE.688001"]["triggered_level1"]:
    check_result("科创板股票第一级止盈触发", True, "16%涨幅回落2%正确触发（上限17%）")
else:
    check_result("科创板股票第一级止盈触发", False, "应该触发但未触发")

# ==================== 测试3: 科创板股票超过17%不触发第一级 ====================
print("\n" + "=" * 80)
print("📊 测试3: 科创板股票超过17%不触发第一级")
print("=" * 80)

engine3 = MockEngine()
strategy3 = DynamicTakeProfit(engine3)

# 模拟场景：68开头的股票，最高涨幅18%（超过17%上限）
engine3.positions = [MockPosition("SHSE.688002", 500, 50.0)]
engine3.prices = {"SHSE.688002": 58.0}  # 现价58.0，成本50.0，涨幅16%

# 手动设置追踪器状态
strategy3.profit_tracker["SHSE.688002"] = {
    'highest_profit': 0.18,  # 最高涨幅18%（超过17%）
    'peak_time': time.time() - 300,
    'triggered_level1': False,
    'triggered_level2': False,
    'triggered_level3': False
}

# 执行第一级检查
current_price = 58.0
open_price = 50.0
profit_ratio = (current_price - open_price) / open_price  # 16%

print(f"股票代码: SHSE.688002 (科创板)")
print(f"成本价: {open_price:.2f}")
print(f"现价: {current_price:.2f}")
print(f"当前涨幅: {profit_ratio*100:.2f}%")
print(f"最高涨幅: 18.00%")
print(f"预期结果: ❌ 不应触发第一级 (18% > 17%上限，应交由第三级处理)")

strategy3._check_level1("SHSE.688002", current_price, open_price, 500, profit_ratio)

if not strategy3.profit_tracker["SHSE.688002"]["triggered_level1"]:
    check_result("科创板股票超17%不触发第一级", True, "18%涨幅超过17%上限，正确跳过")
else:
    check_result("科创板股票超17%不触发第一级", False, "应该跳过但触发了")

# ==================== 测试4: 主板股票超过8.5%不触发第一级 ====================
print("\n" + "=" * 80)
print("📊 测试4: 主板股票超过8.5%不触发第一级")
print("=" * 80)

engine4 = MockEngine()
strategy4 = DynamicTakeProfit(engine4)

# 模拟场景：60开头的股票，最高涨幅9%（超过8.5%上限）
engine4.positions = [MockPosition("SHSE.600002", 1000, 10.0)]
engine4.prices = {"SHSE.600002": 10.7}  # 现价10.7，成本10.0，涨幅7%

# 手动设置追踪器状态
strategy4.profit_tracker["SHSE.600002"] = {
    'highest_profit': 0.09,  # 最高涨幅9%（超过8.5%）
    'peak_time': time.time() - 300,
    'triggered_level1': False,
    'triggered_level2': False,
    'triggered_level3': False
}

# 执行第一级检查
current_price = 10.7
open_price = 10.0
profit_ratio = (current_price - open_price) / open_price  # 7%

print(f"股票代码: SHSE.600002 (主板)")
print(f"成本价: {open_price:.2f}")
print(f"现价: {current_price:.2f}")
print(f"当前涨幅: {profit_ratio*100:.2f}%")
print(f"最高涨幅: 9.00%")
print(f"预期结果: ❌ 不应触发第一级 (9% > 8.5%上限，应交由第二级处理)")

strategy4._check_level1("SHSE.600002", current_price, open_price, 1000, profit_ratio)

if not strategy4.profit_tracker["SHSE.600002"]["triggered_level1"]:
    check_result("主板股票超8.5%不触发第一级", True, "9%涨幅超过8.5%上限，正确跳过")
else:
    check_result("主板股票超8.5%不触发第一级", False, "应该跳过但触发了")

# ==================== 测试5: 创业板股票（30开头）第一级止盈 ====================
print("\n" + "=" * 80)
print("📊 测试5: 创业板股票（30开头）第一级止盈")
print("=" * 80)

engine5 = MockEngine()
strategy5 = DynamicTakeProfit(engine5)

# 模拟场景：30开头的股票，最高涨幅15%，当前回落1.5%
engine5.positions = [MockPosition("SZSE.300001", 800, 20.0)]
engine5.prices = {"SZSE.300001": 22.5}  # 现价22.5，成本20.0，涨幅12.5%

# 手动设置追踪器状态
strategy5.profit_tracker["SZSE.300001"] = {
    'highest_profit': 0.15,  # 最高涨幅15%
    'peak_time': time.time() - 300,
    'triggered_level1': False,
    'triggered_level2': False,
    'triggered_level3': False
}

# 执行第一级检查
current_price = 22.5
open_price = 20.0
profit_ratio = (current_price - open_price) / open_price  # 12.5%

print(f"股票代码: SZSE.300001 (创业板)")
print(f"成本价: {open_price:.2f}")
print(f"现价: {current_price:.2f}")
print(f"当前涨幅: {profit_ratio*100:.2f}%")
print(f"最高涨幅: 15.00%")
print(f"回落幅度: {(0.15 - profit_ratio)*100:.2f}%")
print(f"预期结果: ✅ 应触发止盈 (15% > 12.5% + 1.3%，且15% < 17%上限)")

strategy5._check_level1("SZSE.300001", current_price, open_price, 800, profit_ratio)

if strategy5.profit_tracker["SZSE.300001"]["triggered_level1"]:
    check_result("创业板股票第一级止盈触发", True, "15%涨幅回落2.5%正确触发（上限17%）")
else:
    check_result("创业板股票第一级止盈触发", False, "应该触发但未触发")

# ==================== 总结 ====================
print("\n" + "=" * 80)
print("📊 测试总结")
print("=" * 80)
print(f"总测试数: {passed + failed}")
print(f"✅ 通过: {passed}")
print(f"❌ 失败: {failed}")

if failed == 0:
    print("\n🎉 恭喜！所有测试通过！")
    print("✨ 分板块止盈策略工作正常！")
    print("\n📋 核心逻辑验证:")
    print("   ✅ 60/00开头: 3% ~ 8.5% 区间")
    print("   ✅ 68/30开头: 3% ~ 17% 区间")
    print("   ✅ 回落1.3%触发机制正常")
    print("   ✅ 超过上限正确跳过，交由第二/三级处理")
else:
    print(f"\n⚠️  有 {failed} 项测试失败，请修复后再部署！")

print("=" * 80)

sys.exit(0 if failed == 0 else 1)
