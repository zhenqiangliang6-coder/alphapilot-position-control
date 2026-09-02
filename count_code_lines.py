"""
AlphaPilot 策略项目代码统计工具
统计核心模块的代码行数、注释行数和空行分布
"""
import os
from pathlib import Path

def count_lines(file_path):
    """统计文件的代码行、注释行和空行"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        total = len(lines)
        code = len([l for l in lines if l.strip() and not l.strip().startswith('#')])
        comment = len([l for l in lines if l.strip().startswith('#')])
        empty = len([l for l in lines if not l.strip()])
        
        return {'total': total, 'code': code, 'comment': comment, 'empty': empty}
    except Exception as e:
        return {'total': 0, 'code': 0, 'comment': 0, 'empty': 0}

def main():
    # 核心业务文件列表
    core_files = [
        'main.py',
        'core/trader_engine.py',
        'risk/stop_loss.py',
        'risk/dynamic_take_profit.py',
        'strategies/rocket_boost.py',
        'strategies/signal_strategy.py',
        'strategies/auction_strategy.py',
        'strategies/delayed_strategy.py',
        'core/state_manager.py',
        'utils/helpers.py',
        'utils/logger.py',
        'listener.py',
    ]
    
    print('='*70)
    print('📊 AlphaPilot Pro 策略项目代码统计报告')
    print('='*70)
    print()
    
    stats_list = []
    for file_rel_path in core_files:
        file_path = Path(__file__).parent / file_rel_path
        if file_path.exists():
            stats = count_lines(file_path)
            stats['name'] = file_rel_path
            stats_list.append(stats)
    
    # 按总行数排序
    stats_list.sort(key=lambda x: x['total'], reverse=True)
    
    # 打印详细统计
    for stats in stats_list:
        print(f"📄 {stats['name']}")
        print(f"   总行数: {stats['total']:4d} | 代码: {stats['code']:4d} | "
              f"注释: {stats['comment']:3d} | 空行: {stats['empty']:3d}")
        print()
    
    # 汇总统计
    total_all = sum(s['total'] for s in stats_list)
    total_code = sum(s['code'] for s in stats_list)
    total_comment = sum(s['comment'] for s in stats_list)
    total_empty = sum(s['empty'] for s in stats_list)
    
    print('='*70)
    print(f'✅ 核心模块总计 ({len(stats_list)} 个文件):')
    print(f'   总行数:   {total_all:5d} 行')
    print(f'   有效代码: {total_code:5d} 行 ({total_code/total_all*100:.1f}%)')
    print(f'   注释文档: {total_comment:5d} 行 ({total_comment/total_all*100:.1f}%)')
    print(f'   空白行:   {total_empty:5d} 行 ({total_empty/total_all*100:.1f}%)')
    print('='*70)
    
    # 统计整个项目
    print()
    project_root = Path(__file__).parent
    all_py_files = list(project_root.rglob('*.py'))
    all_py_files = [f for f in all_py_files 
                    if 'quant_env' not in str(f) and '__pycache__' not in str(f)]
    
    project_total = 0
    for py_file in all_py_files:
        stats = count_lines(py_file)
        project_total += stats['total']
    
    print(f'🌟 整个项目总计 ({len(all_py_files)} 个Python文件):')
    print(f'   总行数: {project_total} 行')
    print('='*70)

if __name__ == '__main__':
    main()
