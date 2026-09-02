"""
动态止盈诊断工具 - 检查当前持仓的止盈状态

功能：
1. 显示所有持仓的当前盈亏比例
2. 检查哪些股票达到了各级止盈阈值
3. 验证止盈模块是否正常工作
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from gm.api import *

def diagnose_take_profit():
    """诊断动态止盈状态"""
    
    print("="*70)
    print("🔍 AlphaPilot Pro - 动态止盈诊断工具")
    print("="*70)
    print()
    
    # 设置Token
    from config import settings
    set_token(settings.GM_TOKEN)
    
    # 查询持仓
    positions = get_position()
    
    if not positions:
        print("❌ 当前无持仓")
        return
    
    print(f"📊 当前持仓数量: {len(positions)} 只股票")
    print()
    
    # 止盈阈值
    level1_threshold = 0.03   # 3%
    level2_threshold = 0.09   # 9%
    level3_threshold = 0.18   # 18%
    
    print("="*70)
    print("📈 持仓盈亏分析")
    print("="*70)
    print()
    
    reached_level1 = []
    reached_level2 = []
    reached_level3 = []
    no_profit = []
    
    for pos in positions:
        volume = pos.get('volume', 0)
        if volume <= 0:
            continue
        
        code = pos.get('symbol', '')
        can_sell = pos.get('available_now', 0)
        
        # 获取成本价（优先级: vwap_open > vwap > cost/volume）
        vwap_open = pos.get('vwap_open', 0.0)
        vwap = pos.get('vwap', 0.0)
        cost = pos.get('cost', 0.0)
        
        if vwap_open and vwap_open > 0:
            open_price = vwap_open
        elif vwap and vwap > 0:
            open_price = vwap
        elif cost > 0 and volume > 0:
            open_price = cost / volume
        else:
            print(f"⚠️  {code}: 无法获取成本价")
            continue
        
        # 获取最新价格
        current_price = pos.get('last_price', open_price)
        
        if current_price <= 0:
            current_price = open_price
        
        # 计算盈亏
        profit_ratio = (current_price - open_price) / open_price
        profit_amount = (current_price - open_price) * volume
        
        # 判断是否达到止盈级别
        status = []
        if profit_ratio >= level3_threshold:
            status.append("✅ L3强势股止盈")
            reached_level3.append(code)
        elif profit_ratio >= level2_threshold:
            status.append("✅ L2波段止盈")
            reached_level2.append(code)
        elif profit_ratio >= level1_threshold:
            status.append("✅ L1快速止盈")
            reached_level1.append(code)
        else:
            status.append("⏸️  未达止盈阈值")
            no_profit.append(code)
        
        # T+1状态
        t1_status = "可卖" if can_sell > 0 else "今日买入(T+1)"
        
        # 输出信息
        print(f"📄 {code}")
        print(f"   持仓: {volume}股 | 可卖: {can_sell}股 ({t1_status})")
        print(f"   成本: ¥{open_price:.2f} → 现价: ¥{current_price:.2f}")
        print(f"   盈亏: {profit_ratio*100:+.2f}% (¥{profit_amount:+.2f})")
        print(f"   状态: {' '.join(status)}")
        print()
    
    # 汇总统计
    print("="*70)
    print("📊 止盈状态汇总")
    print("="*70)
    print()
    print(f"✅ 达到L1快速止盈(≥3%):  {len(reached_level1)} 只")
    if reached_level1:
        for code in reached_level1:
            print(f"   - {code}")
    print()
    
    print(f"✅ 达到L2波段止盈(≥9%):  {len(reached_level2)} 只")
    if reached_level2:
        for code in reached_level2:
            print(f"   - {code}")
    print()
    
    print(f"✅ 达到L3强势止盈(≥18%): {len(reached_level3)} 只")
    if reached_level3:
        for code in reached_level3:
            print(f"   - {code}")
    print()
    
    print(f"⏸️  未达止盈阈值(<3%):    {len(no_profit)} 只")
    if no_profit:
        for code in no_profit:
            print(f"   - {code}")
    print()
    
    print("="*70)
    print("💡 诊断结论")
    print("="*70)
    print()
    
    total_reached = len(reached_level1) + len(reached_level2) + len(reached_level3)
    
    if total_reached == 0:
        print("ℹ️  当前所有持仓均未达到止盈阈值（最低需要涨3%）")
        print("   止盈模块正在正常监控中，一旦有股票涨到3%就会触发")
        print()
        print("📌 建议:")
        print("   1. 继续持有，等待股价上涨")
        print("   2. 如果想降低止盈阈值，可以修改 config/settings.py 中的配置")
    else:
        print(f"✅ 有 {total_reached} 只股票已达到止盈阈值")
        print()
        
        # 检查是否有可卖数量
        can_sell_count = 0
        for pos in positions:
            if pos.get('available_now', 0) > 0:
                code = pos.get('symbol', '')
                if code in reached_level1 or code in reached_level2 or code in reached_level3:
                    can_sell_count += 1
        
        if can_sell_count > 0:
            print(f"⚠️  其中 {can_sell_count} 只股票可以卖出（非今日买入）")
            print("   如果这些股票满足回落条件，止盈模块会自动执行卖出")
        else:
            print("⚠️  所有达到止盈阈值的股票都是今日买入（T+1限制）")
            print("   这些股票明天才能卖出，止盈模块会持续监控")
    
    print()
    print("="*70)

if __name__ == '__main__':
    diagnose_take_profit()
