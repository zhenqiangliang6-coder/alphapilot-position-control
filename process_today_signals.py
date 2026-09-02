# -*- coding: utf-8 -*-
"""
批量处理今日信号文件，生成延时策略观察名单
作者: Qoder + 梁子羿团队
日期: 2026-05-20
"""

import os
import sys
import json
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from strategies.delayed_strategy import DelayedStrategy
from utils.logger import init_logger
from config import settings


class MockEngine:
    """模拟引擎对象（仅用于加载配置）"""
    pass


def process_today_signals():
    """处理今天的所有信号文件"""
    
    print("=" * 80)
    print("📊 批量处理今日信号 - 生成延时策略观察名单")
    print("=" * 80)
    print()
    
    # 初始化日志系统
    try:
        init_logger(settings.LOG_DIR)
        print("✅ 日志系统已初始化")
    except Exception as e:
        print(f"⚠️  日志初始化失败（不影响处理）: {e}")
    
    # 初始化延时策略
    mock_engine = MockEngine()
    delayed_strat = DelayedStrategy(mock_engine)
    
    print(f"✅ 延时策略已初始化")
    print(f"   - 配置文件: {delayed_strat.personalities_file}")
    print(f"   - 观察名单: {delayed_strat.watchlist_file}")
    print(f"   - 延时股票总数: {len([k for k, v in delayed_strat.stock_personalities.items() if v.get('type') == 'delayed'])}")
    print()
    
    # 查找今天的信号文件
    signal_dir = os.path.join("signals", "processed")
    today_str = datetime.now().strftime("%Y%m%d")
    
    signal_files = [
        f for f in os.listdir(signal_dir) 
        if f.startswith(f"signal_batch_{today_str}") and f.endswith(".txt")
    ]
    
    signal_files.sort()  # 按时间排序
    
    print(f"📁 找到 {len(signal_files)} 个今天的信号文件")
    print()
    
    # 统计变量
    total_signals = 0
    delayed_candidates = 0
    added_to_watchlist = 0
    skipped_by_vr = 0
    already_in_list = 0
    
    # 处理每个文件
    for filename in signal_files:
        filepath = os.path.join(signal_dir, filename)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            # 解析 JSONL 格式
            signals = []
            if content.startswith('['):
                signals = json.loads(content)
                if not isinstance(signals, list):
                    signals = [signals]
            else:
                for line in content.split('\n'):
                    if not line.strip():
                        continue
                    try:
                        sig = json.loads(line)
                        signals.append(sig)
                    except:
                        continue
            
            # 处理每个信号
            for sig in signals:
                code = sig.get('code', '')
                action = sig.get('action') or sig.get('signal', '')
                price = float(sig.get('price', 0) or sig.get('current_price', 0))
                vr = float(sig.get('volume_ratio', 0))
                
                if not code or action != 'BUY':
                    continue
                
                total_signals += 1
                
                # 提取纯数字代码
                pure_code = code.split('.')[-1] if '.' in code else code
                
                # 检查是否为延时股票
                config = delayed_strat.stock_personalities.get(pure_code, 
                             delayed_strat.stock_personalities.get(code, {}))
                
                if config.get('type') != 'delayed':
                    continue
                
                delayed_candidates += 1
                
                # 量比过滤
                min_vr = config.get('min_volume_ratio', 18.0)
                if vr < min_vr:
                    skipped_by_vr += 1
                    continue
                
                # 尝试加入观察名单
                result = delayed_strat.process_signal(code, action, price, vr)
                
                if result:
                    added_to_watchlist += 1
                    stock_name = config.get('name', code)
                    target_date = delayed_strat.delayed_watchlist['watchlist'][code]['target_date']
                    print(f"✅ [{filename[:30]}] {code} ({stock_name}) - 已加入观察名单，目标日: {target_date}")
                else:
                    already_in_list += 1
        
        except Exception as e:
            print(f"❌ 处理文件 {filename} 失败: {e}")
    
    # 输出统计结果
    print()
    print("=" * 80)
    print("📈 处理结果统计")
    print("=" * 80)
    print(f"总信号数:           {total_signals}")
    print(f"延时股票候选:       {delayed_candidates}")
    print(f"量比不达标跳过:     {skipped_by_vr}")
    print(f"已在名单中跳过:     {already_in_list}")
    print(f"新加入观察名单:     {added_to_watchlist}")
    print()
    
    # 显示当前观察名单
    watchlist = delayed_strat.delayed_watchlist.get('watchlist', {})
    print(f"📋 当前观察名单 ({len(watchlist)} 只股票):")
    print("-" * 80)
    
    if watchlist:
        for code, item in sorted(watchlist.items()):
            name = item.get('name', code)
            signal_date = item.get('signal_date', '')
            target_date = item.get('target_date', '')
            trigger_vr = item.get('trigger_volume_ratio', 0)
            target_vr = item.get('target_day_min_vr', 0.2)
            print(f"  {code:12s} {name:10s} | 信号日:{signal_date} → 目标日:{target_date} | VR:{trigger_vr:.2f}→{target_vr:.2f}")
    else:
        print("  (空)")
    
    print()
    print("=" * 80)
    print("✨ 处理完成！明天这些股票将在目标日自动检查买入条件")
    print("=" * 80)


if __name__ == "__main__":
    process_today_signals()
