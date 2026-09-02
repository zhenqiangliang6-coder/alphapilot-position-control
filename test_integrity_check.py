# -*- coding: utf-8 -*-
"""
系统完整性检查脚本 - V10.0 分时段量比策略升级后验证
Alphapilot智能体团队
检查日期: 2026-05-18

检查项目:
1. signal_strategy.py 模块导入测试
2. 关键方法存在性检查
3. 方法签名兼容性验证
4. main.py 调用路径检查
"""

import sys
import os
import inspect

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("🔍 AlphaPilot Pro V10.0 系统完整性检查")
print("=" * 80)

passed = 0
failed = 0
warnings = 0

def check_result(test_name, result, detail=""):
    global passed, failed, warnings
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

# ==================== 测试1: 模块导入 ====================
print("\n" + "=" * 80)
print("📦 测试1: 核心模块导入")
print("=" * 80)

# 【关键修复】先初始化日志系统
try:
    from utils.logger import init_logger, get_logger
    import tempfile
    temp_log_dir = tempfile.mkdtemp()
    init_logger(temp_log_dir)
    print(f"✅ 日志系统初始化成功 (临时目录: {temp_log_dir})")
except Exception as e:
    print(f"⚠️  日志系统初始化失败（不影响测试）: {e}")

try:
    from strategies.signal_strategy import SignalStrategy
    check_result("signal_strategy 模块导入", True)
except Exception as e:
    check_result("signal_strategy 模块导入", False, str(e))
    sys.exit(1)

try:
    from strategies.delayed_strategy import DelayedStrategy
    check_result("delayed_strategy 模块导入", True)
except Exception as e:
    check_result("delayed_strategy 模块导入", False, str(e))

try:
    from core.trader_engine import TraderEngine
    check_result("trader_engine 模块导入", True)
except Exception as e:
    check_result("trader_engine 模块导入", False, str(e))

# ==================== 测试2: SignalStrategy 类实例化 ====================
print("\n" + "=" * 80)
print("🏗️  测试2: SignalStrategy 类结构")
print("=" * 80)

class MockEngine:
    """模拟交易引擎"""
    def query_asset(self):
        return {'cash': 100000}
    def query_positions(self):
        return []
    def order_stock(self, *args):
        return True

try:
    mock_engine = MockEngine()
    strategy = SignalStrategy(mock_engine)
    check_result("SignalStrategy 实例化", True)
except Exception as e:
    check_result("SignalStrategy 实例化", False, str(e))
    sys.exit(1)

# ==================== 测试3: 关键方法存在性检查 ====================
print("\n" + "=" * 80)
print("🔧 测试3: 关键方法存在性")
print("=" * 80)

required_methods = [
    '__init__',
    'set_delayed_strategy',
    '_get_index_change',
    'process_single_signal',
    'process_files',
    '_execute_signal',
    '_decide_action',
    '_check_repeat_protection',
    '_check_position_and_calculate_volume'
]

for method_name in required_methods:
    if hasattr(strategy, method_name):
        method = getattr(strategy, method_name)
        if callable(method):
            check_result(f"方法存在: {method_name}", True)
        else:
            check_result(f"方法存在: {method_name}", False, "不是可调用对象")
    else:
        check_result(f"方法存在: {method_name}", False, "方法不存在")

# ==================== 测试4: 方法签名兼容性 ====================
print("\n" + "=" * 80)
print("📝 测试4: 方法签名兼容性")
print("=" * 80)

# 检查 _decide_action 方法签名
try:
    sig = inspect.signature(strategy._decide_action)
    params = list(sig.parameters.keys())
    
    # 应该包含 action 和 vr 两个参数
    if 'action' in params and 'vr' in params:
        check_result("_decide_action 方法签名", True, f"参数: {params}")
    else:
        check_result("_decide_action 方法签名", False, f"缺少必要参数，当前参数: {params}")
except Exception as e:
    check_result("_decide_action 方法签名", False, str(e))

# 检查 process_single_signal 方法签名
try:
    sig = inspect.signature(strategy.process_single_signal)
    params = list(sig.parameters.keys())
    
    if 'signal_file_path' in params:
        check_result("process_single_signal 方法签名", True, f"参数: {params}")
    else:
        check_result("process_single_signal 方法签名", False, f"缺少必要参数，当前参数: {params}")
except Exception as e:
    check_result("process_single_signal 方法签名", False, str(e))

# 检查 set_delayed_strategy 方法签名
try:
    sig = inspect.signature(strategy.set_delayed_strategy)
    params = list(sig.parameters.keys())
    
    if 'delayed_strat' in params:
        check_result("set_delayed_strategy 方法签名", True, f"参数: {params}")
    else:
        check_result("set_delayed_strategy 方法签名", False, f"缺少必要参数，当前参数: {params}")
except Exception as e:
    check_result("set_delayed_strategy 方法签名", False, str(e))

# ==================== 测试5: _decide_action 逻辑测试 ====================
print("\n" + "=" * 80)
print("🧪 测试5: _decide_action 决策逻辑")
print("=" * 80)

# Mock大盘数据获取
original_get_index = strategy._get_index_change
def mock_get_index_positive():
    return 0.5  # 大盘上涨0.5%

def mock_get_index_negative():
    return -0.65  # 大盘下跌0.65%

strategy._get_index_change = mock_get_index_positive

# 测试场景1: 早盘正常市场买入
try:
    import datetime
    original_now = datetime.datetime.now
    
    class MockTime:
        @staticmethod
        def now():
            return original_now().replace(hour=9, minute=45)
    
    datetime.datetime = MockTime
    
    result = strategy._decide_action("BUY", 1.8)
    if result:
        check_result("早盘正常市场买入(VR=1.8)", True, "应通过 (阈值1.5)")
    else:
        check_result("早盘正常市场买入(VR=1.8)", False, "应通过但被拦截")
    
    datetime.datetime = original_now
except Exception as e:
    check_result("早盘正常市场买入(VR=1.8)", False, str(e))
    datetime.datetime = original_now

# 测试场景2: 早盘正常市场买入 - 量比不足
try:
    datetime.datetime = MockTime
    result = strategy._decide_action("BUY", 1.2)
    if not result:
        check_result("早盘正常市场买入(VR=1.2)", True, "应拦截 (阈值1.5)")
    else:
        check_result("早盘正常市场买入(VR=1.2)", False, "应拦截但通过了")
    
    datetime.datetime = original_now
except Exception as e:
    check_result("早盘正常市场买入(VR=1.2)", False, str(e))
    datetime.datetime = original_now

# 测试场景3: 弱势市场买入
strategy._get_index_change = mock_get_index_negative

try:
    datetime.datetime = MockTime
    result = strategy._decide_action("BUY", 2.5)
    if result:
        check_result("早盘弱势市场买入(VR=2.5)", True, "应通过 (阈值2.25)")
    else:
        check_result("早盘弱势市场买入(VR=2.5)", False, "应通过但被拦截")
    
    datetime.datetime = original_now
except Exception as e:
    check_result("早盘弱势市场买入(VR=2.5)", False, str(e))
    datetime.datetime = original_now

# 恢复原始方法
strategy._get_index_change = original_get_index

# ==================== 测试6: main.py 调用路径检查 ====================
print("\n" + "=" * 80)
print("🔗 测试6: main.py 调用路径")
print("=" * 80)

main_py_path = os.path.join(os.path.dirname(__file__), 'main.py')
if os.path.exists(main_py_path):
    try:
        with open(main_py_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查关键调用
        checks = [
            ('SignalStrategy 导入', 'from strategies.signal_strategy import SignalStrategy'),
            ('signal_strat 实例化', 'signal_strat = SignalStrategy(engine)'),
            ('set_delayed_strategy 调用', 'signal_strat.set_delayed_strategy(delayed_strat)'),
            ('register_consumer 注册', 'signal_bus.register_consumer(signal_strat.process_single_signal)'),
        ]
        
        for check_name, check_str in checks:
            if check_str in content:
                check_result(f"main.py: {check_name}", True)
            else:
                check_result(f"main.py: {check_name}", False, f"未找到: {check_str}")
    except Exception as e:
        check_result("main.py 文件读取", False, str(e))
else:
    check_result("main.py 文件存在", False, "文件不存在")

# ==================== 总结 ====================
print("\n" + "=" * 80)
print("📊 完整性检查总结")
print("=" * 80)
print(f"总测试数: {passed + failed}")
print(f"✅ 通过: {passed}")
print(f"❌ 失败: {failed}")
print(f"⚠️  警告: {warnings}")

if failed == 0:
    print("\n🎉 恭喜！所有完整性检查通过！")
    print("✨ V10.0 分时段量比策略升级成功，未影响其他功能！")
else:
    print(f"\n⚠️  有 {failed} 项检查失败，请修复后再部署！")

print("=" * 80)

# 返回退出码
sys.exit(0 if failed == 0 else 1)
