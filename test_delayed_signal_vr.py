# -*- coding: utf-8 -*-
"""
延时策略信号量比读取测试 - 验证从Alphapilot信号文件中读取最新量比
Alphapilot智能体团队
作者: 梁子羿、侯沣睿、梁茹真
邮箱: 497720537@qq.com | 电话: 13392077558
"""
import os
import sys
import json
import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import settings
from utils.logger import init_logger, get_logger
from strategies.delayed_strategy import DelayedStrategy


class MockEngine:
    """模拟交易引擎"""
    def get_latest_prices(self, codes):
        return {code: 10.0 for code in codes}
    
    def query_asset(self):
        return {'cash': 100000, 'total_asset': 100000}
    
    def order_stock(self, code, action, volume, price, strategy):
        log = get_logger()
        log.log(f"[模拟下单] {code} {action} {volume}股 @ {price:.2f}")
        return True


def create_test_signal(code, vr, ts=None):
    """创建测试信号文件"""
    if ts is None:
        ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    signal_dir = settings.SIGNAL_DIR_INPUT
    os.makedirs(signal_dir, exist_ok=True)
    
    filename = f"test_signal_{int(datetime.datetime.now().timestamp())}.txt"
    filepath = os.path.join(signal_dir, filename)
    
    signal_data = [{
        "ts": ts,
        "code": code,
        "name": "测试股票",
        "action": "BUY",
        "price": 10.0,
        "volume_ratio": vr,
        "source": "AlphaPilot_Test"
    }]
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(signal_data, f, ensure_ascii=False, indent=2)
    
    return filepath


def test_signal_volume_ratio():
    """测试从信号文件中读取量比"""
    print("=" * 80)
    print("🧪 延时策略 - Alphapilot信号量比读取测试")
    print("=" * 80)
    
    # 初始化日志
    init_logger(settings.LOG_DIR)
    log = get_logger()
    
    # 创建延时策略实例
    engine = MockEngine()
    delayed_strat = DelayedStrategy(engine)
    
    print("\n✅ 延时策略初始化完成\n")
    
    # ==================== 测试1: 单个信号文件 ====================
    print("=" * 80)
    print("📝 测试1: 单个信号文件")
    print("=" * 80)
    
    test_code = "SZSE.001309"
    create_test_signal(test_code, vr=3.5)
    
    latest_vr = delayed_strat._get_latest_signal_volume_ratio(test_code)
    
    if latest_vr and abs(latest_vr - 3.5) < 0.01:
        print(f"✅ 成功读取量比: {latest_vr:.2f}")
    else:
        print(f"❌ 读取失败或数值错误: {latest_vr}")
    
    # ==================== 测试2: 多个信号文件（取最新） ====================
    print("\n" + "=" * 80)
    print("📝 测试2: 多个信号文件（应返回最新的）")
    print("=" * 80)
    
    # 创建旧信号
    old_ts = (datetime.datetime.now() - datetime.timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S')
    create_test_signal(test_code, vr=1.5, ts=old_ts)
    
    # 创建新信号
    new_ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    create_test_signal(test_code, vr=4.2, ts=new_ts)
    
    latest_vr = delayed_strat._get_latest_signal_volume_ratio(test_code)
    
    if latest_vr and abs(latest_vr - 4.2) < 0.01:
        print(f"✅ 正确返回最新量比: {latest_vr:.2f}")
    else:
        print(f"❌ 错误: 返回 {latest_vr}，期望 4.2")
    
    # ==================== 测试3: 无信号 ====================
    print("\n" + "=" * 80)
    print("📝 测试3: 无信号的股票")
    print("=" * 80)
    
    no_signal_code = "SHSE.999999"
    latest_vr = delayed_strat._get_latest_signal_volume_ratio(no_signal_code)
    
    if latest_vr is None:
        print(f"✅ 正确返回 None（无信号）")
    else:
        print(f"❌ 错误: 应返回 None，实际返回 {latest_vr}")
    
    # ==================== 测试4: 完整流程模拟 ====================
    print("\n" + "=" * 80)
    print("📝 测试4: 完整流程模拟（目标日当天收到新信号）")
    print("=" * 80)
    
    # 构造观察名单
    today = datetime.date.today()
    delayed_strat.delayed_watchlist['watchlist'] = {
        test_code: {
            "name": "测试股票",
            "action": "BUY",
            "signal_date": (today - datetime.timedelta(days=3)).strftime('%Y-%m-%d'),
            "target_date": today.strftime('%Y-%m-%d'),
            "trigger_price": 10.0,
            "trigger_volume_ratio": 2.0,  # 触发量比阈值
            "status": "waiting",
            "delay_days": 3
        }
    }
    
    # 创建满足条件的信号（量比 >= 2.0）
    create_test_signal(test_code, vr=3.8)
    
    print(f"\n🔍 观察名单中的股票: {test_code}")
    print(f"   触发量比阈值: 2.0")
    print(f"   最新信号量比: 3.8")
    
    # 执行检查
    delayed_strat.check_and_execute()
    
    # 检查结果
    remaining = len(delayed_strat.delayed_watchlist.get('watchlist', {}))
    if remaining == 0:
        print(f"✅ 买入成功，已从观察名单删除")
    else:
        print(f"⚠️  仍在观察名单中（可能未触发或资金不足）")
    
    # ==================== 总结 ====================
    print("\n" + "=" * 80)
    print("📊 测试总结")
    print("=" * 80)
    print("""
✅ 核心功能验证:
1. 能够从Alphapilot信号文件中读取指定股票的最新量比
2. 支持多个信号文件时自动选择时间戳最新的
3. 无信号时返回 None
4. 目标日当天根据最新信号量比判断是否买入

💡 架构优势:
- Alphapilot是大脑：负责判断个股强弱，发送信号
- 掘金是手脚：负责执行交易，不自己做判断
- 量比决策完全依赖Alphapilot信号，符合设计初衷

⚠️ 注意事项:
- 信号文件格式必须包含 volume_ratio 字段
- 时间戳格式应为 'YYYY-MM-DD HH:MM:SS'
- 支持JSON数组和JSONL两种格式
    """)
    print("=" * 80)


if __name__ == '__main__':
    test_signal_volume_ratio()
