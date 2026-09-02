# -*- coding: utf-8 -*-
"""
测试掘金SDK持仓字段 - T+1可平数量验证
Alphapilot智能体团队
作者: 梁子羿、侯沣睿、梁茹真
邮箱: 497720537@qq.com | 电话: 13392077558

用途：在掘金策略框架内测试Position对象的字段，确认可平数量字段的正确性
运行方式：在掘金量化终端中运行此策略
"""
from gm.api import *
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def init(context):
    """策略初始化函数"""
    print("\n" + "="*80)
    print("🧪 掘金SDK持仓字段测试工具 - T+1可平数量验证")
    print("Alphapilot智能体团队 | 497720537@qq.com | 13392077558")
    print("="*80 + "\n")
    
    # 订阅沪深300指数（确保能收到行情，激活策略运行）
    subscribe(symbols='SHSE.000300', frequency='60s', count=1)
    
    # 延迟2秒后执行测试（确保系统完全初始化及交易通道连接）
    import threading
    timer = threading.Timer(2.0, test_position_fields)
    timer.start()


def test_position_fields():
    """测试持仓对象的所有字段"""
    
    print("=" * 80)
    print("📊 开始测试持仓字段")
    print("=" * 80)
    print()
    
    try:
        # 查询持仓（返回的是字典列表，不是Position对象）
        positions = get_position()
        
        if not positions:
            print("⚠️  当前无持仓，无法测试")
            print("💡 建议：请先买入一些股票，然后再次运行此策略")
            print("\n" + "="*80)
            print("✅ 测试完成（无持仓）")
            print("="*80)
            return
        
        print(f"✅ 当前持仓数量: {len(positions)} 只股票\n")
        
        for i, pos in enumerate(positions, 1):
            print(f"{'='*80}")
            print(f"📈 持仓 #{i}")
            print(f"{'='*80}")
            
            # pos 是字典类型，不是Position对象
            print(f"\n【数据类型】")
            print(f"  类型: {type(pos)}")
            print(f"  是否为字典: {isinstance(pos, dict)}")
            
            # 基本信息（使用字典键访问）
            print(f"\n【基本信息】")
            symbol = pos.get('symbol', 'N/A')
            print(f"  股票代码 (symbol): {symbol}")
            
            # 尝试其他可能的代码字段
            stock_code = pos.get('stock_code', None)
            code = pos.get('code', None)
            if stock_code:
                print(f"  股票代码 (stock_code): {stock_code}")
            if code:
                print(f"  股票代码 (code): {code}")
            
            # 持仓数量（关键！）
            print(f"\n【持仓数量 - 核心字段】")
            volume = pos.get('volume', 0)
            print(f"  📦 总持仓 (volume): {volume} 股")
            
            # 尝试获取可平数量
            available = pos.get('available', None)
            can_use_volume = pos.get('can_use_volume', None)
            
            if available is not None:
                print(f"  ✅ 可平数量 (available): {available} 股")
            else:
                print(f"  ❌ 可平数量 (available): 字段不存在")
            
            if can_use_volume is not None:
                print(f"  ✅ 可平数量 (can_use_volume): {can_use_volume} 股")
            else:
                print(f"  ❌ 可平数量 (can_use_volume): 字段不存在")
            
            # 今日买入数量（如果可获取）
            today_buy = pos.get('today_buy_volume', None)
            today_vol = pos.get('today_vol', None)
            if today_buy is not None:
                print(f"  📊 今日买入 (today_buy_volume): {today_buy} 股")
            if today_vol is not None:
                print(f"  📊 今日买入 (today_vol): {today_vol} 股")
            
            # 验证T+1逻辑
            print(f"\n【T+1合规验证】")
            if available is not None:
                if available == 0:
                    print(f"  ⚠️  今日买入，不可卖出（T+1限制）")
                elif available < volume:
                    print(f"  ⚠️  部分可卖：{available}/{volume} 股")
                    print(f"  💡 今日买入: {volume - available} 股（不可卖）")
                else:
                    print(f"  ✅ 全部可卖：{available} 股")
            else:
                print(f"  ❌ 无法获取可平数量，T+1检查可能失败！")
            
            # 其他信息
            print(f"\n【价格与盈亏】")
            cost = pos.get('cost', 0) or pos.get('cost_price', 0)
            vwap = pos.get('vwap', 0)
            vwap_open = pos.get('vwap_open', 0)
            last_price = pos.get('last_price', 0)
            market_value = pos.get('market_value', 0)
            fpnl = pos.get('fpnl', 0)
            
            print(f"  成本价 (cost): {cost:.2f} 元")
            print(f"  VWAP (vwap): {vwap:.2f} 元")
            print(f"  VWAP_Open (vwap_open): {vwap_open:.2f} 元")
            print(f"  最新价 (last_price): {last_price:.2f} 元")
            print(f"  持仓市值 (market_value): {market_value:.2f} 元")
            print(f"  浮动盈亏 (fpnl): {fpnl:.2f} 元")
            
            # 列出所有可用字段
            print(f"\n【完整字段列表】")
            keys = list(pos.keys())
            print(f"  可用字段 ({len(keys)}个):")
            for key in sorted(keys):
                value = pos[key]
                # 格式化显示
                if isinstance(value, float):
                    print(f"    {key}: {value:.4f}")
                else:
                    print(f"    {key}: {value}")
            
            print()
        
        print("=" * 80)
        print("✅ 测试完成！")
        print("=" * 80)
        print()
        print("📝 总结：")
        print("  1. 确认哪个字段代表'可平数量'（available 或 can_use_volume）")
        print("  2. 验证T+1逻辑是否正确（今日买入不可卖）")
        print("  3. 更新代码中所有卖出操作使用该字段")
        print()
        print("💡 提示：测试完成后，可以在掘金终端中停止策略")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


def on_bar(context, bars):
    """K线数据回调（本测试不需要具体逻辑，但需存在以维持策略运行）"""
    pass


if __name__ == '__main__':
    """
    掘金量化策略启动入口
    
    参数说明:
        strategy_id: 策略ID，必须与掘金终端中创建的策略实例ID一致
        filename: 文件名，使用相对路径（与本文件名保持一致）
        mode: 运行模式 - MODE_LIVE(实时) / MODE_BACKTEST(回测)
        token: 绑定计算机的ID，可在系统设置-密钥管理中生成
    """
    run(strategy_id='c2dd98da-3d5a-11f1-962d-1ece51d839d6',
        filename='test_position_fields.py',
        mode=MODE_LIVE,
        token='fdf08e9d00c4da3b635c2616724ddae3f7793562')