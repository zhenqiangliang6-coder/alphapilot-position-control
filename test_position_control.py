def test_position_control():
    """测试仓位控制功能"""
    
    print("=" * 60)
    print("🧪 轻量级仓位控制模块 - 快速测试")
    print("=" * 60)
    
    # ⭐ 先初始化日志系统（必须）
    from utils.logger import init_logger
    os.makedirs("logs", exist_ok=True)
    init_logger("logs")
    
    # 创建mock engine
    class MockEngine:
        pass
    
    mock_engine = MockEngine()
    
    # 1. 测试默认信号加载（从D:\ESC\ESC\forecast_report.html）
    print("\n[测试1] 从HTML文件加载信号")
    pc = PositionControl(engine=mock_engine)
    print(f"  初始信号: {pc.position_signal}")
    print(f"  仓位系数: {pc.position_ratio * 100:.0f}%")
    
    # 2. 测试仓位上限检查
    print("\n[测试2] 仓位上限检查逻辑")
    
    # 假设总资产300万
    total_asset = 3000000
    
    # 场景A: 当前持仓90万（30%），信号为下跌-1（上限30%）
    print("\n  场景A: 总资金300万，持仓90万(30%)")
    print("  信号: 下跌-1 (仓位上限30%)")
    
    allowed, current_ratio, max_ratio = pc.check_buy_allowed(900000, total_asset)
    print(f"  → 允许买入: {allowed} | 当前: {current_ratio*100:.1f}% | 上限: {max_ratio*100:.0f}%")
    
    # 场景B: 当前持仓150万（50%），信号仍为下跌-1（上限30%）
    print("\n  场景B: 总资金300万，持仓150万(50%)")
    print("  信号: 下跌-1 (仓位上限30%)")
    
    allowed, current_ratio, max_ratio = pc.check_buy_allowed(1500000, total_asset)
    print(f"  → 允许买入: {allowed} | 当前: {current_ratio*100:.1f}% | 上限: {max_ratio*100:.0f}%")
    
    # 场景C: 卖出后剩60万（20%），信号仍为下跌-1（上限30%）
    print("\n  场景C: 总资金300万，持仓60万(20%)")
    print("  信号: 下跌-1 (仓位上限30%)")
    
    allowed, current_ratio, max_ratio = pc.check_buy_allowed(600000, total_asset)
    print(f"  → 允许买入: {allowed} | 当前: {current_ratio*100:.1f}% | 上限: {max_ratio*100:.0f}%")
    
    # 场景D: 信号变为上涨1（上限100%）
    pc.position_signal = 1
    pc._update_position_ratio()
    print("\n  场景D: 总资金300万，持仓150万(50%)")
    print("  信号: 上涨1 (仓位上限100%)")
    
    allowed, current_ratio, max_ratio = pc.check_buy_allowed(1500000, total_asset)
    print(f"  → 允许买入: {allowed} | 当前: {current_ratio*100:.1f}% | 上限: {max_ratio*100:.0f}%")
    
    # 3. 测试手动设置信号
    print("\n[测试3] 手动设置信号值")
    
    test_signals = [1, 0, -1]
    
    for signal_val in test_signals:
        pc.position_signal = signal_val
        pc._update_position_ratio()
        print(f"  信号 {signal_val}: 仓位系数 = {pc.position_ratio * 100:.0f}%")
    
    print("\n" + "=" * 60)
    print("✅ 测试完成！")
    print("=" * 60)
