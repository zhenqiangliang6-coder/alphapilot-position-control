# -*- coding: utf-8 -*-
"""
精英名单诊断工具 - 检查竞价卖出失败原因
Alphapilot智能体团队
作者: 梁子羿、侯沣睿、梁茹真
邮箱: 497720537@qq.com | 电话: 13392077558

使用方法:
    python diagnose_auction_sell.py
"""

import os
import sys
import json
import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import settings

def diagnose_elite_list():
    """诊断精英名单状态"""
    
    print("=" * 80)
    print("🔍 AlphaPilot 精英名单诊断工具")
    print("=" * 80)
    print()
    
    # 1. 检查当前时间
    now = datetime.datetime.now()
    current_time_str = now.strftime("%H%M")
    current_time_display = now.strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"📅 当前时间: {current_time_display}")
    print(f"⏰ 时间字符串: {current_time_str}")
    
    is_auction_window = "0921" <= current_time_str <= "0925"
    is_trading = ("0930" <= current_time_str <= "1130") or ("1300" <= current_time_str <= "1500")
    
    if is_auction_window:
        print(f"✅ [竞价窗口] 当前在不可撤单竞价时段(09:21-09:25)")
    elif is_trading:
        print(f"ℹ️ [交易时间] 当前在正常交易时段")
    else:
        print(f"⚠️ [非交易时间] 当前不在交易时段")
    
    print()
    
    # 2. 检查精英名单文件
    state_file = settings.STATE_FILE
    print(f"📁 精英名单文件: {state_file}")
    
    if not os.path.exists(state_file):
        print(f"❌ 文件不存在: {state_file}")
        print(f"💡 提示: 精英名单文件将在尾盘14:40-15:00重建时创建")
        return
    
    try:
        with open(state_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            
            # 检查文件是否为空
            if not content:
                print(f"❌ 文件为空")
                print()
                print("💡 可能原因:")
                print("  1. 尾盘重建尚未执行（当前时间不在14:40-15:00）")
                print("  2. 昨日无符合条件的持仓（浮盈>{:.0f}%）".format(settings.ELITE_PROFIT_THRESHOLD*100))
                print("  3. 文件被意外清空或损坏")
                print()
                print("🔍 建议操作:")
                print("  1. 等待今日尾盘14:40-15:00自动重建")
                print("  2. 或手动触发重建（重启策略并在尾盘时段运行）")
                return
            
            data = json.loads(content)
        
        elite_list = data.get('positions', {})
        
        print(f"📊 精英名单数量: {len(elite_list)} 只")
        print()
        
        if not elite_list:
            print("ℹ️ 精英名单为空")
            return
        
        print("=" * 80)
        print("📋 精英名单详情:")
        print("=" * 80)
        print(f"{'股票代码':<15} {'持仓数量':<10} {'浮盈比例':<10} {'成本价':<10} {'收盘价':<10}")
        print("-" * 80)
        
        for code, info in elite_list.items():
            volume = info.get('volume', 0)
            profit_ratio = info.get('profit_ratio', 0)
            cost_price = info.get('cost_price', 0)
            close_price = info.get('close_price', 0)
            
            print(f"{code:<15} {volume:<10} {profit_ratio*100:<10.2f}% {cost_price:<10.2f} {close_price:<10.2f}")
        
        print()
        
        # 3. 分析未卖出原因
        print("=" * 80)
        print("🔍 未卖出原因分析:")
        print("=" * 80)
        
        if is_auction_window:
            print("✅ 当前在不可撤单竞价窗口(09:21-09:25)，理论上应该执行卖出")
            print()
            print("可能的原因:")
            print("  1. ❌ 策略未在运行（检查掘金IDE是否启动）")
            print("  2. ❌ on_bar回调未触发（行情数据未更新）")
            print("  3. ❌ executed_today标志已为True（今日已执行过）")
            print("  4. ❌ 持仓不存在或可卖数量为0")
            print()
            print("建议操作:")
            print("  1. 检查掘金IDE是否正在运行")
            print("  2. 查看日志文件，搜索'[心跳-竞价]'关键字")
            print("  3. 重启策略（新的一天会自动重置executed_today标志）")
        
        elif is_trading:
            print("⚠️ 当前已过不可撤单竞价时间窗口(09:21-09:25)")
            print()
            print("说明:")
            print("  - 集合竞价卖出仅在09:21-09:25不可撤单时段执行")
            print("  - 避免09:15-09:20的假单干扰，确保成交价格真实可靠")
            print("  - 这些股票将在明日09:21-09:25自动卖出")
            print()
            print("✅ 已修复：竞价策略现在通过心跳线程主动触发")
            print("   - 不再依赖on_bar回调（可能不触发）")
            print("   - 每5秒检查一次竞价时间窗口")
            print("   - 覆盖所有持仓股票（无论是否订阅）")
            print()
            print("备选方案:")
            print("  1. ⏳ 等待明日竞价时段自动卖出")
            print("  2. 📈 如果盘中涨幅达到止盈条件，动态止盈策略会卖出")
            print("  3. 📉 如果盘中跌幅达到止损条件，止损策略会卖出")
            print("  4. 🔄 如果收到新的信号，信号策略可能卖出")
        
        else:
            print("⚠️ 当前非交易时间")
            print()
            print("说明:")
            print("  - 竞价卖出将在下一个交易日09:15-09:30执行")
            print()
            print("建议:")
            print("  - 无需操作，系统会在明日自动处理")
        
        print()
        
        # 4. 检查日志文件
        log_dir = "logs"
        if os.path.exists(log_dir):
            log_files = [f for f in os.listdir(log_dir) if f.endswith('.log')]
            if log_files:
                latest_log = max(log_files, key=lambda f: os.path.getmtime(os.path.join(log_dir, f)))
                print(f"📝 最新日志文件: {latest_log}")
                print(f"💡 提示: 查看日志中的'[竞价]'相关记录以获取更多信息")
        
        print()
        print("=" * 80)
        print("✅ 诊断完成")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ 读取精英名单文件失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    diagnose_elite_list()
