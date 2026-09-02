# -*- coding: utf-8 -*-
"""
延时策略资金不足场景测试 - 验证宽限期机制
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
    """模拟交易引擎（用于测试）"""
    def __init__(self, cash=0):
        self.cash = cash
    
    def get_latest_prices(self, codes):
        """返回模拟价格"""
        return {code: 10.0 for code in codes}
    
    def query_asset(self):
        """模拟资产查询"""
        return {'cash': self.cash, 'total_asset': self.cash}
    
    def order_stock(self, code, action, volume, price, strategy):
        """模拟下单"""
        log = get_logger()
        if self.cash >= volume * price:
            log.log(f"[模拟下单] {code} {action} {volume}股 @ {price:.2f} - 成功")
            self.cash -= volume * price
            return True
        else:
            log.log(f"[模拟下单] {code} {action} {volume}股 @ {price:.2f} - 失败（资金不足: {self.cash:.2f})")
            return False


def test_insufficient_funds():
    """测试资金不足时的宽限期机制"""
    print("=" * 80)
    print("🧪 延时策略 - 资金不足场景测试")
    print("=" * 80)
    
    # 初始化日志
    init_logger(settings.LOG_DIR)
    log = get_logger()
    
    # 清空观察名单
    watchlist_file = os.path.join(settings.DATA_DIR, "delayed_watchlist.json")
    with open(watchlist_file, 'w', encoding='utf-8') as f:
        json.dump({"last_update": "", "watchlist": {}}, f, indent=2)
    print("\n🗑️  已清空观察名单\n")
    
    # ==================== 场景1: 目标日当天资金充足 ====================
    print("=" * 80)
    print("📝 场景1: 目标日当天，资金充足（50000元）")
    print("=" * 80)
    
    engine_rich = MockEngine(cash=50000)
    delayed_strat_rich = DelayedStrategy(engine_rich)
    
    # 手动构造一个已到目标日的观察名单
    today = datetime.date.today()
    delayed_strat_rich.delayed_watchlist['watchlist'] = {
        "600821": {
            "name": "金发科技",
            "action": "BUY",
            "signal_date": (today - datetime.timedelta(days=4)).strftime('%Y-%m-%d'),
            "target_date": today.strftime('%Y-%m-%d'),
            "trigger_price": 10.0,
            "trigger_volume_ratio": 2.0,
            "status": "waiting",
            "delay_days": 4,
            "grace_days": 3
        }
    }
    
    print(f"\n🔍 检查前观察名单: {len(delayed_strat_rich.delayed_watchlist['watchlist'])}只")
    delayed_strat_rich.check_and_execute()
    print(f"🔍 检查后观察名单: {len(delayed_strat_rich.delayed_watchlist['watchlist'])}只")
    
    if len(delayed_strat_rich.delayed_watchlist['watchlist']) == 0:
        print("✅ 资金充足时，买入成功后从名单删除（正确）")
    else:
        print("❌ 异常：资金充足应该买入成功并删除")
    
    # ==================== 场景2: 目标日当天资金不足 ====================
    print("\n" + "=" * 80)
    print("📝 场景2: 目标日当天，资金不足（仅5000元）")
    print("=" * 80)
    
    engine_poor = MockEngine(cash=5000)
    delayed_strat_poor = DelayedStrategy(engine_poor)
    
    # 手动构造观察名单
    delayed_strat_poor.delayed_watchlist['watchlist'] = {
        "600821": {
            "name": "金发科技",
            "action": "BUY",
            "signal_date": (today - datetime.timedelta(days=4)).strftime('%Y-%m-%d'),
            "target_date": today.strftime('%Y-%m-%d'),
            "trigger_price": 10.0,
            "trigger_volume_ratio": 2.0,
            "status": "waiting",
            "delay_days": 4,
            "grace_days": 3
        }
    }
    
    print(f"\n🔍 检查前观察名单: {len(delayed_strat_poor.delayed_watchlist['watchlist'])}只")
    delayed_strat_poor.check_and_execute()
    print(f"🔍 检查后观察名单: {len(delayed_strat_poor.delayed_watchlist['watchlist'])}只")
    
    if len(delayed_strat_poor.delayed_watchlist['watchlist']) == 1:
        print("✅ 资金不足时，保留在观察名单继续尝试（正确）")
        
        # 检查是否仍在宽限期内
        item = delayed_strat_poor.delayed_watchlist['watchlist']['600821']
        signal_date = datetime.datetime.strptime(item['signal_date'], '%Y-%m-%d').date()
        days_since_signal = (today - signal_date).days
        max_days = item.get('delay_days', 1) + item.get('grace_days', 3)
        
        print(f"   📊 距信号日: {days_since_signal}天 | 最大允许: {max_days}天")
        if days_since_signal <= max_days:
            print("   ✅ 仍在宽限期内，明日可继续尝试")
        else:
            print("   ❌ 已超出宽限期，应该被删除")
    else:
        print("❌ 异常：资金不足时应保留在名单中")
    
    # ==================== 场景3: 超出宽限期 ====================
    print("\n" + "=" * 80)
    print("📝 场景3: 超出宽限期（信号日距今8天 > delay_days(4) + grace_days(3)）")
    print("=" * 80)
    
    engine_expired = MockEngine(cash=5000)
    delayed_strat_expired = DelayedStrategy(engine_expired)
    
    # 构造已过期的观察名单
    old_signal_date = today - datetime.timedelta(days=8)
    old_target_date = today - datetime.timedelta(days=4)
    
    delayed_strat_expired.delayed_watchlist['watchlist'] = {
        "600821": {
            "name": "金发科技",
            "action": "BUY",
            "signal_date": old_signal_date.strftime('%Y-%m-%d'),
            "target_date": old_target_date.strftime('%Y-%m-%d'),
            "trigger_price": 10.0,
            "trigger_volume_ratio": 2.0,
            "status": "waiting",
            "delay_days": 4,
            "grace_days": 3
        }
    }
    
    print(f"\n🔍 检查前观察名单: {len(delayed_strat_expired.delayed_watchlist['watchlist'])}只")
    print(f"   信号日: {old_signal_date} | 目标日: {old_target_date} | 今天: {today}")
    print(f"   距信号日: 8天 | 最大允许: 7天 (4+3)")
    
    delayed_strat_expired.check_and_execute()
    print(f"🔍 检查后观察名单: {len(delayed_strat_expired.delayed_watchlist['watchlist'])}只")
    
    if len(delayed_strat_expired.delayed_watchlist['watchlist']) == 0:
        print("✅ 超出宽限期后，自动从名单删除（正确）")
    else:
        print("❌ 异常：超出宽限期应该删除")
    
    # ==================== 总结 ====================
    print("\n" + "=" * 80)
    print("📊 测试总结")
    print("=" * 80)
    print("""
✅ 修复后的行为:
1. 目标日当天资金充足 → 买入成功 → 从名单删除
2. 目标日当天资金不足 → 买入失败 → 保留在名单（宽限期内）
3. 宽限期内每天继续尝试买入
4. 超出宽限期（delay_days + grace_days）→ 自动删除

💡 宽限期机制优势:
- 避免因临时资金不足永久错过机会
- 给账户资金周转留出缓冲时间
- 防止观察名单无限积累（有明确过期时间）
- 默认3天宽限期，可根据需要调整

⚠️ 注意事项:
- 宽限期内每天都会尝试买入（消耗API调用）
- 如果长期资金不足，建议手动清理观察名单
- 可通过修改 grace_days 字段调整宽限期长度
    """)
    print("=" * 80)


if __name__ == '__main__':
    test_insufficient_funds()
