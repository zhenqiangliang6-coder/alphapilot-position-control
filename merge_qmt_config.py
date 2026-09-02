# -*- coding: utf-8 -*-
"""
合并 QMT 延时配置到 stock_personalities.json
作者: Qoder + 梁子羿团队
日期: 2026-05-20

功能：
1. 将 qmt_delay_config.json 中的延时股票配置合并到 stock_personalities.json
2. 已有股票：更新配置（以 qmt 为准）
3. 新股票：追加到 stock_personalities
4. 自动备份原文件
"""

import json
import os
from datetime import datetime


def merge_qmt_to_stock_personalities():
    """合并 QMT 配置到 stock_personalities"""
    
    print("=" * 80)
    print("🔄 合并 QMT 延时配置到 stock_personalities.json")
    print("=" * 80)
    print()
    
    # 文件路径
    qmt_file = "data/qmt_delay_config.json"
    stock_file = "data/stock_personalities.json"
    
    # 加载配置文件
    print("📂 加载配置文件...")
    with open(qmt_file, 'r', encoding='utf-8') as f:
        qmt_data = json.load(f)
    print(f"   ✅ qmt_delay_config.json: {len(qmt_data)} 只股票")
    
    with open(stock_file, 'r', encoding='utf-8') as f:
        stock_data = json.load(f)
    print(f"   ✅ stock_personalities.json: {len(stock_data)} 只股票")
    print()
    
    # 统计分析
    qmt_codes = set(qmt_data.keys())
    stock_codes = set(stock_data.keys())
    
    new_codes = qmt_codes - stock_codes  # 需要新增的
    update_codes = qmt_codes & stock_codes  # 需要更新的
    keep_codes = stock_codes - qmt_codes  # 保持不变的
    
    print("📊 合并分析:")
    print(f"   - 新增股票: {len(new_codes)} 只")
    print(f"   - 更新股票: {len(update_codes)} 只")
    print(f"   - 保持不变: {len(keep_codes)} 只")
    print()
    
    # 显示新增股票
    if new_codes:
        print("➕ 将新增以下股票:")
        for code in sorted(new_codes):
            name = qmt_data[code].get('name', '未知')
            delay_days = qmt_data[code].get('delay_days', 1)
            min_vr = qmt_data[code].get('min_volume_ratio', 0)
            print(f"   {code:10s} {name:10s} (延迟{delay_days}天, min_vr={min_vr})")
        print()
    
    # 显示更新股票
    if update_codes:
        print("🔄 将更新以下股票:")
        for code in sorted(update_codes):
            old_type = stock_data[code].get('type', 'unknown')
            new_type = qmt_data[code].get('type', 'unknown')
            old_vr = stock_data[code].get('min_volume_ratio', 0)
            new_vr = qmt_data[code].get('min_volume_ratio', 0)
            
            if old_vr != new_vr or old_type != new_type:
                name = qmt_data[code].get('name', stock_data[code].get('name', '未知'))
                print(f"   {code:10s} {name:10s} VR:{old_vr:.2f}→{new_vr:.2f}")
        print()
    
    # 确认操作
    print("⚠️  此操作将修改 stock_personalities.json")
    confirm = input("是否继续？(y/n): ").strip().lower()
    
    if confirm != 'y':
        print("❌ 操作已取消")
        return
    
    # 备份原文件
    backup_file = f"data/stock_personalities.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    print(f"\n💾 备份原文件到: {backup_file}")
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(stock_data, f, ensure_ascii=False, indent=2)
    print("   ✅ 备份完成")
    print()
    
    # 执行合并
    print("🔧 开始合并...")
    
    updated_count = 0
    added_count = 0
    
    # 1. 更新已有股票
    for code in update_codes:
        # 保留 stock_personalities 中可能存在的额外字段
        existing_extra_fields = {
            k: v for k, v in stock_data[code].items() 
            if k not in ['name', 'type', 'delay_days', 'min_volume_ratio', 'target_day_min_vr', 'note']
        }
        
        # 使用 qmt 的配置覆盖标准字段
        stock_data[code] = {
            'name': qmt_data[code].get('name', stock_data[code].get('name')),
            'type': qmt_data[code].get('type', 'delayed'),
            'delay_days': qmt_data[code].get('delay_days', 1),
            'min_volume_ratio': qmt_data[code].get('min_volume_ratio', 0.5),
            'target_day_min_vr': qmt_data[code].get('target_day_min_vr', 0.2),
            'note': qmt_data[code].get('note', '')
        }
        
        # 恢复额外字段
        stock_data[code].update(existing_extra_fields)
        
        updated_count += 1
    
    # 2. 添加新股票
    for code in new_codes:
        stock_data[code] = {
            'name': qmt_data[code].get('name', ''),
            'type': qmt_data[code].get('type', 'delayed'),
            'delay_days': qmt_data[code].get('delay_days', 1),
            'min_volume_ratio': qmt_data[code].get('min_volume_ratio', 0.5),
            'target_day_min_vr': qmt_data[code].get('target_day_min_vr', 0.2),
            'note': qmt_data[code].get('note', '')
        }
        added_count += 1
    
    # 保存合并后的文件
    print(f"\n💾 保存合并结果...")
    with open(stock_file, 'w', encoding='utf-8') as f:
        json.dump(stock_data, f, ensure_ascii=False, indent=2)
    print(f"   ✅ 已保存到: {stock_file}")
    print()
    
    # 验证结果
    print("=" * 80)
    print("✅ 合并完成统计")
    print("=" * 80)
    print(f"更新股票: {updated_count} 只")
    print(f"新增股票: {added_count} 只")
    print(f"总股票数: {len(stock_data)} 只")
    print()
    
    # 验证延时股票数量
    delayed_count = len([k for k, v in stock_data.items() if v.get('type') == 'delayed'])
    print(f"延时股票总数: {delayed_count} 只")
    print()
    
    print("✨ 所有操作完成！系统将在下次启动时加载新配置")
    print("=" * 80)


if __name__ == "__main__":
    try:
        merge_qmt_to_stock_personalities()
    except Exception as e:
        print(f"\n❌ 合并失败: {e}")
        import traceback
        traceback.print_exc()
