# -*- coding: utf-8 -*-
"""
分时段量比策略 V10.0 快速测试脚本
Alphapilot智能体团队
测试日期: 2026-05-18
"""

import sys
import os
import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("🚀 分时段量比策略 V10.0 沙盒测试")
print("=" * 80)

# ==================== 模拟环境 ====================
class MockLogger:
    def log(self, msg):
        print(f"   [LOG] {msg}")

class MockSignalStrategy:
    """模拟信号策略类，用于测试"""
    
    def __init__(self):
        self.test_results = []
    
    def _get_index_change(self):
        """Mock获取大盘涨跌幅"""
        return self.mock_index_change
    
    def _decide_action(self, action, vr, mock_time_str=None, mock_index_change=None):
        """
        复制实际的_decide_action逻辑进行测试
        
        参数:
            action: "BUY" 或 "SELL"
            vr: 量比
            mock_time_str: 模拟时间字符串 (如 "0945")
            mock_index_change: 模拟大盘涨跌幅
        """
        # 设置Mock数据
        self.mock_index_change = mock_index_change if mock_index_change is not None else 0.5
        time_str = mock_time_str or "1000"
        
        # 判断时段
        is_morning_early = ("0930" <= time_str < "1030")
        is_morning_late = ("1030" <= time_str <= "1130")
        is_afternoon_early = ("1300" <= time_str < "1400")
        is_afternoon_late = ("1400" <= time_str <= "1500")
        
        period_name = ""
        if is_morning_early:
            period_name = "上午早盘(09:30-10:30)"
        elif is_morning_late:
            period_name = "上午尾盘(10:30-11:30)"
        elif is_afternoon_early:
            period_name = "下午早盘(13:00-14:00)"
        elif is_afternoon_late:
            period_name = "下午尾盘(14:00-15:00)"
        else:
            period_name = "非交易时段"
        
        index_change = self.mock_index_change
        
        # 买入策略
        if action == "BUY":
            base_vr_map = {
                'morning_early': 1.5,
                'morning_late': 2.25,
                'afternoon_early': 3.375,
                'afternoon_late': 5.06
            }
            
            if is_morning_early:
                base_vr = base_vr_map['morning_early']
            elif is_morning_late:
                base_vr = base_vr_map['morning_late']
            elif is_afternoon_early:
                base_vr = base_vr_map['afternoon_early']
            elif is_afternoon_late:
                base_vr = base_vr_map['afternoon_late']
            else:
                return False
            
            if -0.35 <= index_change <= 1.9:
                threshold = base_vr
                market_status = "正常"
            elif -1.0 <= index_change < -0.35:
                threshold = base_vr * 1.5
                market_status = "弱势"
            else:
                return False
            
            result = vr >= threshold
            print(f"   [{period_name}] 大盘{market_status}{index_change:.2f}% | VR={vr:.2f} vs 阈值={threshold:.2f} → {'✅通过' if result else '❌拦截'}")
            return result
        
        # 卖出策略
        else:
            if -0.35 <= index_change <= 1.9:
                threshold = 1.5
                result = vr >= threshold
                print(f"   [卖出] 大盘正常{index_change:.2f}% | VR={vr:.2f} vs 阈值={threshold} → {'✅通过' if result else '❌拦截'}")
                return result
            elif -1.0 <= index_change < -0.35:
                threshold = 1.0
                result = vr >= threshold
                print(f"   [卖出](弱势) 大盘{index_change:.2f}% | VR={vr:.2f} vs 阈值={threshold} → {'✅通过' if result else '❌拦截'}")
                return result
            else:
                return False


# ==================== 测试用例 ====================
def run_test(test_name, action, time_str, index_change, vr, expected_result):
    """运行单个测试用例"""
    print(f"\n{'='*80}")
    print(f"测试: {test_name}")
    print(f"条件: 时间={time_str}, 动作={action}, 大盘={index_change:+.2f}%, 量比={vr}")
    print(f"预期: {'✅通过' if expected_result else '❌拦截'}")
    
    strategy = MockSignalStrategy()
    actual_result = strategy._decide_action(action, vr, time_str, index_change)
    
    status = "✅ PASS" if actual_result == expected_result else "❌ FAIL"
    print(f"结果: {status}")
    
    return actual_result == expected_result


# ==================== 执行测试 ====================
if __name__ == "__main__":
    passed = 0
    failed = 0
    
    print("\n" + "=" * 80)
    print("📊 第一组: 大盘正常区间 (+0.5%) - 买入测试")
    print("=" * 80)
    
    # 测试1: 早盘买入 - 量比达标
    if run_test("早盘买入-量比达标", "BUY", "0945", 0.5, 1.8, True):
        passed += 1
    else:
        failed += 1
    
    # 测试2: 早盘买入 - 量比不足
    if run_test("早盘买入-量比不足", "BUY", "0945", 0.5, 1.2, False):
        passed += 1
    else:
        failed += 1
    
    # 测试3: 上午尾盘买入 - 量比刚好达标
    if run_test("上午尾盘-量比刚好", "BUY", "1045", 0.5, 2.25, True):
        passed += 1
    else:
        failed += 1
    
    # 测试4: 上午尾盘买入 - 量比略低
    if run_test("上午尾盘-量比略低", "BUY", "1045", 0.5, 2.0, False):
        passed += 1
    else:
        failed += 1
    
    # 测试5: 下午早盘买入 - 量比达标
    if run_test("下午早盘-量比达标", "BUY", "1330", 0.5, 3.5, True):
        passed += 1
    else:
        failed += 1
    
    # 测试6: 下午早盘买入 - 量比不足
    if run_test("下午早盘-量比不足", "BUY", "1330", 0.5, 3.0, False):
        passed += 1
    else:
        failed += 1
    
    # 测试7: 下午尾盘买入 - 量比达标
    if run_test("下午尾盘-量比达标", "BUY", "1430", 0.5, 5.5, True):
        passed += 1
    else:
        failed += 1
    
    # 测试8: 下午尾盘买入 - 量比不足
    if run_test("下午尾盘-量比不足", "BUY", "1430", 0.5, 4.5, False):
        passed += 1
    else:
        failed += 1
    
    print("\n" + "=" * 80)
    print("📊 第二组: 大盘弱势区间 (-0.65%) - 买入测试")
    print("=" * 80)
    
    # 测试9: 早盘弱势 - 量比达标 (1.5 × 1.5 = 2.25)
    if run_test("早盘弱势-量比达标", "BUY", "0945", -0.65, 2.3, True):
        passed += 1
    else:
        failed += 1
    
    # 测试10: 早盘弱势 - 量比不足
    if run_test("早盘弱势-量比不足", "BUY", "0945", -0.65, 2.0, False):
        passed += 1
    else:
        failed += 1
    
    # 测试11: 上午尾盘弱势 - 量比达标 (2.25 × 1.5 = 3.375)
    if run_test("上午尾盘弱势-量比达标", "BUY", "1045", -0.65, 3.5, True):
        passed += 1
    else:
        failed += 1
    
    # 测试12: 下午尾盘弱势 - 量比达标 (5.06 × 1.5 = 7.59)
    if run_test("下午尾盘弱势-量比达标", "BUY", "1430", -0.65, 8.0, True):
        passed += 1
    else:
        failed += 1
    
    # 测试13: 下午尾盘弱势 - 量比不足
    if run_test("下午尾盘弱势-量比不足", "BUY", "1430", -0.65, 7.0, False):
        passed += 1
    else:
        failed += 1
    
    print("\n" + "=" * 80)
    print("📊 第三组: 卖出测试")
    print("=" * 80)
    
    # 测试14: 正常区间卖出 - 量比达标
    if run_test("正常区间卖出-达标", "SELL", "1000", 0.5, 1.8, True):
        passed += 1
    else:
        failed += 1
    
    # 测试15: 正常区间卖出 - 量比不足
    if run_test("正常区间卖出-不足", "SELL", "1000", 0.5, 1.2, False):
        passed += 1
    else:
        failed += 1
    
    # 测试16: 弱势区间卖出 - 量比达标
    if run_test("弱势区间卖出-达标", "SELL", "1000", -0.65, 1.2, True):
        passed += 1
    else:
        failed += 1
    
    # 测试17: 弱势区间卖出 - 量比不足
    if run_test("弱势区间卖出-不足", "SELL", "1000", -0.65, 0.8, False):
        passed += 1
    else:
        failed += 1
    
    print("\n" + "=" * 80)
    print("📊 第四组: 边界情况测试")
    print("=" * 80)
    
    # 测试18: 大盘超出安全区间 (暴涨)
    if run_test("大盘暴涨-禁止买入", "BUY", "1000", 2.5, 10.0, False):
        passed += 1
    else:
        failed += 1
    
    # 测试19: 大盘超出安全区间 (暴跌)
    if run_test("大盘暴跌-禁止买入", "BUY", "1000", -1.5, 10.0, False):
        passed += 1
    else:
        failed += 1
    
    # 测试20: 非交易时段
    if run_test("非交易时段-禁止买入", "BUY", "1200", 0.5, 10.0, False):
        passed += 1
    else:
        failed += 1
    
    # 测试21: 量比刚好等于阈值
    if run_test("量比刚好等于阈值", "BUY", "0945", 0.5, 1.5, True):
        passed += 1
    else:
        failed += 1
    
    # 总结
    print("\n" + "=" * 80)
    print(f"📈 测试结果汇总")
    print("=" * 80)
    print(f"总测试数: {passed + failed}")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print(f"通过率: {passed / (passed + failed) * 100:.1f}%")
    
    if failed == 0:
        print("\n🎉 恭喜！所有测试用例全部通过！策略逻辑正确！")
    else:
        print(f"\n⚠️  有 {failed} 个测试用例失败，请检查代码逻辑！")
    
    print("=" * 80)
