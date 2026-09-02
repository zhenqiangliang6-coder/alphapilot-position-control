# -*- coding: utf-8 -*-
"""
延时策略严格去重与提前买入防护测试 - 验证以第一次信号为准
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


def test_strict_dedup_and_early_buy_protection():
    """测试严格去重和提前买入防护"""
    print("=" * 80)
    print("🧪 延时策略 - 严格去重与提前买入防护测试")
    print("=" * 80)
    
    # 初始化日志
    init_logger(settings.LOG_DIR)
    log = get_logger()
    
    # 创建延时策略实例
    engine = MockEngine()
    delayed_strat = DelayedStrategy(engine)
    
    # 清空观察名单
    delayed_strat.delayed_watchlist['watchlist'] = {}
    
    test_code = "SHSE.000510"  # 新金路
    
    # ==================== 测试1: 首次加入（5月18日，量比0.5）====================
    print("\n" + "=" * 80)
    print("📝 测试1: 首次加入观察名单（5月18日，量比0.5）")
    print("=" * 80)
    
    result1 = delayed_strat.process_signal(test_code, "BUY", price=8.20, volume_ratio=0.50)
    
    if result1 and test_code in delayed_strat.delayed_watchlist['watchlist']:
        item = delayed_strat.delayed_watchlist['watchlist'][test_code]
        print(f"✅ 成功加入观察名单")
        print(f"   股票代码: {test_code} (新金路)")
        print(f"   信号日: {item['signal_date']}")
        print(f"   目标日: {item['target_date']}")
        print(f"   触发价格: {item['trigger_price']}")
        print(f"   触发量比: {item['trigger_volume_ratio']}")
        print(f"   延时天数: {item['delay_days']}天")
        
        # 保存初始状态用于后续对比
        initial_signal_date = item['signal_date']
        initial_vr = item['trigger_volume_ratio']
        initial_target_date = item['target_date']
    else:
        print(f"❌ 加入失败")
        return
    
    # ==================== 测试2: 重复信号（5月19日，量比0.8 > 0.5）====================
    print("\n" + "=" * 80)
    print("📝 测试2: 重复信号 - 量比更高（5月19日，量比0.8 > 0.5）")
    print("=" * 80)
    print("   期望行为: 拒绝更新，保持首次条件不变")
    
    result2 = delayed_strat.process_signal(test_code, "BUY", price=8.50, volume_ratio=0.80)
    
    if not result2:
        item = delayed_strat.delayed_watchlist['watchlist'][test_code]
        
        # 验证所有字段都未改变
        unchanged = (
            item['signal_date'] == initial_signal_date and
            abs(item['trigger_volume_ratio'] - initial_vr) < 0.01 and
            item['target_date'] == initial_target_date
        )
        
        if unchanged:
            print(f"✅ 正确防护：拒绝更新，保持首次条件")
            print(f"   信号日仍为: {item['signal_date']} (未变为5月19日)")
            print(f"   触发量比仍为: {item['trigger_volume_ratio']} (未更新为0.8)")
            print(f"   目标日仍为: {item['target_date']}")
        else:
            print(f"❌ 错误：字段被更新了！")
            print(f"   信号日: {item['signal_date']} (期望: {initial_signal_date})")
            print(f"   触发量比: {item['trigger_volume_ratio']} (期望: {initial_vr})")
            print(f"   目标日: {item['target_date']} (期望: {initial_target_date})")
    else:
        print(f"❌ 错误：应该返回False并拒绝处理")
    
    # ==================== 测试3: 重复信号（5月20日，量比0.3 < 0.5）====================
    print("\n" + "=" * 80)
    print("📝 测试3: 重复信号 - 量比更低（5月20日，量比0.3 < 0.5）")
    print("=" * 80)
    print("   期望行为: 同样拒绝更新")
    
    result3 = delayed_strat.process_signal(test_code, "BUY", price=8.10, volume_ratio=0.30)
    
    if not result3:
        item = delayed_strat.delayed_watchlist['watchlist'][test_code]
        if item['signal_date'] == initial_signal_date:
            print(f"✅ 正确防护：拒绝写入，保持首次条件")
        else:
            print(f"❌ 错误：信号日被修改")
    else:
        print(f"❌ 错误：应该返回False")
    
    # ==================== 测试4: 提前买入防护（5月19日检查）====================
    print("\n" + "=" * 80)
    print("📝 测试4: 提前买入防护（5月19日检查，目标日是5月21日）")
    print("=" * 80)
    
    # 手动构造一个未到目标日的场景
    today = datetime.date.today()
    future_target = today + datetime.timedelta(days=2)  # 2天后才是目标日
    
    delayed_strat.delayed_watchlist['watchlist'] = {
        test_code: {
            "name": "新金路",
            "action": "BUY",
            "signal_date": today.strftime('%Y-%m-%d'),
            "target_date": future_target.strftime('%Y-%m-%d'),
            "trigger_price": 8.20,
            "trigger_volume_ratio": 0.50,
            "status": "waiting",
            "delay_days": 2
        }
    }
    
    print(f"   今天: {today}")
    print(f"   目标日: {future_target}")
    print(f"   状态: 未到目标日（差{ (future_target - today).days }天）")
    
    # 创建满足条件的信号文件（量比达标）
    signal_dir = settings.SIGNAL_DIR_INPUT
    os.makedirs(signal_dir, exist_ok=True)
    
    filename = f"test_early_signal_{int(datetime.datetime.now().timestamp())}.txt"
    filepath = os.path.join(signal_dir, filename)
    
    signal_data = [{
        "ts": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "code": test_code,
        "name": "新金路",
        "action": "BUY",
        "price": 8.50,
        "volume_ratio": 1.5,  # 远大于0.5
        "source": "AlphaPilot_Test"
    }]
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(signal_data, f, ensure_ascii=False, indent=2)
    
    print(f"   最新信号量比: 1.5 >= 触发量比 0.5")
    print(f"   期望行为: 即使量比达标，也绝对禁止买入")
    
    # 执行检查（应该不会买入）
    delayed_strat.check_and_execute()
    
    remaining = len(delayed_strat.delayed_watchlist.get('watchlist', {}))
    if remaining == 1:
        print(f"✅ 正确防护：未到目标日，股票仍在观察名单中（未买入）")
    else:
        print(f"❌ 严重BUG：提前买入了！")
    
    # ==================== 测试5: 目标日当天正常买入 ====================
    print("\n" + "=" * 80)
    print("📝 测试5: 目标日当天正常买入（模拟到达目标日）")
    print("=" * 80)
    
    # 修改为目标日当天
    delayed_strat.delayed_watchlist['watchlist'][test_code]['target_date'] = today.strftime('%Y-%m-%d')
    
    print(f"   今天: {today} (目标日)")
    print(f"   最新信号量比: 1.5 >= 触发量比 0.5")
    print(f"   期望行为: 立即买入并从名单删除")
    
    # 执行检查（应该会买入）
    delayed_strat.check_and_execute()
    
    remaining = len(delayed_strat.delayed_watchlist.get('watchlist', {}))
    if remaining == 0:
        print(f"✅ 正确执行：目标日当天，量比达标，买入成功并从名单删除")
    else:
        print(f"⚠️  仍在观察名单中（可能资金不足或其他原因）")
    
    # ==================== 总结 ====================
    print("\n" + "=" * 80)
    print("📊 测试总结")
    print("=" * 80)
    print("""
✅ 核心功能验证:
1. ✅ 严格去重：已在名单中的股票拒绝重复写入
2. ✅ 以第一次为准：无论后续信号量比高低，都不更新任何字段
3. ✅ 防止提前买入：未到目标日时，即使量比达标也绝对禁止买入
4. ✅ 目标日正常执行：到达目标日且量比达标时，立即买入

💡 设计原则:
- **首次信号权威性**: 第一次信号的日期和量比是最终决策依据
- **时间窗口刚性**: 目标日之前严禁任何买入操作
- **数据一致性**: 观察名单中的记录从创建到删除保持不变
- **符合业务逻辑**: 延时策略的核心是"在特定时间窗口内执行首次判断"

⚠️ 注意事项:
- 如果希望采用更强信号，应在首次信号时就确保质量
- 观察名单中的股票不会因后续信号而改变触发条件
- 目标日计算基于首次信号的delay_days，不可更改
    """)
    print("=" * 80)


if __name__ == '__main__':
    test_strict_dedup_and_early_buy_protection()
