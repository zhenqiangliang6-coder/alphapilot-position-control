# -*- coding: utf-8 -*-
"""
AlphaPilot Pro - 独立心跳线程（工业级瘦身版）
Alphapilot智能体团队
作者: 梁子羿、侯沣睿、梁茹真
邮箱: 497720537@qq.com | 电话: 13392077558

职责：
- 每 5 秒输出心跳
- 每 60 秒打印账户信息
- 【新增】每 5 秒执行风控检查（止损/止盈）
"""

import time
import datetime
import threading


class HeartbeatMonitor:
    """独立心跳监控器 - 心跳 + 账户信息 + 风控检查"""
    
    def __init__(self, log_func, account_info_func, stop_loss_mon=None, take_profit_mon=None, auction_strat=None, position_control=None):
        """
        参数:
            log_func: 日志函数
            account_info_func: 账户信息查询函数
            stop_loss_mon: 止损监控器实例（可选）
            take_profit_mon: 动态止盈监控器实例（可选）
            auction_strat: 集合竞价策略实例（可选）
            position_control: 仓位控制器实例（可选）
        """
        self.log = log_func
        self.print_account_info = account_info_func
        self.stop_loss_mon = stop_loss_mon
        self.take_profit_mon = take_profit_mon
        self.auction_strat = auction_strat  # 【新增】竞价策略
        self.position_control = position_control  # ⭐ 新增：仓位控制器
        self.running = False
        self.thread = None
        self.last_account_print = 0
        self.last_stop_loss_check = 0
        self.last_take_profit_check = 0
        self.last_auction_check = 0  # 【新增】上次竞价检查时间
        # 【新增】浮盈汇总相关
        self.last_profit_summary = 0
        self.profit_summary_interval = 180  # 3分钟 = 180秒（可调整为300表示5分钟）
    
    def start(self):
        """启动心跳线程"""
        self.running = True
        self.thread = threading.Thread(
            target=self._heartbeat_loop,
            daemon=True,
            name="HeartbeatMonitor"
        )
        self.thread.start()
        self.log("💓 [心跳] 独立心跳线程已启动（工业级瘦身版 + 风控检查）")
    
    def stop(self):
        """停止心跳线程"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        self.log("🛑 [心跳] 心跳线程已停止")
    
    def _heartbeat_loop(self):
        """心跳循环 - 负责心跳、账户信息和风控检查"""
        while self.running:
            time.sleep(5)
            
            current_time = datetime.datetime.now()
            time_str = current_time.strftime("%H:%M:%S")
            current_ts = time.time()
            
            # 1. 输出心跳（每5秒）
            self.log("💓 [心跳] {} - 系统运行正常".format(time_str))
            
            # 2. 打印账户信息（每60秒，精简版）
            if current_ts - self.last_account_print >= 60:
                try:
                    self.print_account_info()
                    self.last_account_print = current_ts
                except Exception as e:
                    self.log("[警告] 查询账户信息失败: {}".format(e))
            
            # 3. 【新增】止损检查（每15秒，避免频繁检查）
            if self.stop_loss_mon and (current_ts - self.last_stop_loss_check >= 15):
                try:
                    self.stop_loss_mon.check()
                    self.last_stop_loss_check = current_ts
                except Exception as e:
                    self.log("[警告] 止损检查失败: {}".format(e))
            
            # 4. 【新增】动态止盈检查（每15秒）
            if self.take_profit_mon and (current_ts - self.last_take_profit_check >= 15):
                try:
                    # 时间检查已移至 DynamicTakeProfit.check() 内部，避免重复日志
                    self.take_profit_mon.check()
                    self.last_take_profit_check = current_ts
                except Exception as e:
                    self.log("[警告] 止盈检查失败: {}".format(e))
            
            # 5. 【关键修复】集合竞价检查（每5秒，严格限制09:21-09:25不可撤单时段）
            # 解决on_bar回调在竞价时段不触发的问题
            if self.auction_strat and (current_ts - self.last_auction_check >= 5):
                try:
                    current_time_str = current_time.strftime("%H%M")
                    # 【严格限制】只在09:21-09:25不可撤单时段执行，避免09:15-09:20的假单干扰
                    if "0921" <= current_time_str <= "0925":
                        if not self.auction_strat.executed_today:
                            self.log("🔔 [心跳-竞价] 检测到不可撤单竞价时段(09:21-09:25)，主动触发精英名单卖出...")
                            self.auction_strat.execute()
                    self.last_auction_check = current_ts
                except Exception as e:
                    self.log("[警告] 竞价检查失败: {}".format(e))
            
            # 6. 【新增】浮盈汇总输出（每3分钟一次）
            if current_ts - self.last_profit_summary >= self.profit_summary_interval:
                try:
                    self._print_profit_summary()
                    self.last_profit_summary = current_ts
                except Exception as e:
                    self.log("[警告] 浮盈汇总失败: {}".format(e))

    def _print_profit_summary(self):
        """
        打印当前持仓的浮盈汇总
        
        功能：
        - 显示所有持仓股票的盈亏情况
        - 按盈亏比例排序，高亮显示盈利股票
        - 统计整体盈亏状况
        """
        if not self.take_profit_mon or not self.take_profit_mon.engine:
            return
        
        try:
            positions = self.take_profit_mon.engine.query_positions()
            
            if not positions:
                self.log("📊 [浮盈汇总] 当前无持仓")
                return
            
            # 收集所有持仓的盈亏信息
            profit_stocks = []  # 盈利股票
            loss_stocks = []    # 亏损股票
            total_market_value = 0
            total_profit_amount = 0
            
            for pos in positions:
                if pos.volume <= 0:
                    continue
                
                code = pos.stock_code
                volume = pos.volume
                can_sell = pos.can_use_volume
                
                # 获取成本价（兼容多种字段名）
                open_price = getattr(pos, 'open_price', 0.0)
                if open_price <= 0:
                    open_price = getattr(pos, 'cost_price', 0.0)
                if open_price <= 0:
                    open_price = getattr(pos, 'avg_price', 0.0)
                
                if open_price <= 0:
                    continue
                
                # 获取最新价格
                try:
                    latest_prices = self.take_profit_mon.engine.get_latest_prices([code])
                    current_price = latest_prices.get(code)
                    
                    if current_price is None or current_price <= 0:
                        current_price = open_price
                except Exception:
                    continue
                
                # 计算盈亏
                profit_ratio = (current_price - open_price) / open_price
                profit_amount = (current_price - open_price) * volume
                market_value = current_price * volume
                
                total_market_value += market_value
                total_profit_amount += profit_amount
                
                stock_info = {
                    'code': code,
                    'volume': volume,
                    'can_sell': can_sell,
                    'open_price': open_price,
                    'current_price': current_price,
                    'profit_ratio': profit_ratio,
                    'profit_amount': profit_amount,
                    'market_value': market_value
                }
                
                if profit_ratio >= 0:
                    profit_stocks.append(stock_info)
                else:
                    loss_stocks.append(stock_info)
            
            # 按盈亏比例排序
            profit_stocks.sort(key=lambda x: x['profit_ratio'], reverse=True)
            loss_stocks.sort(key=lambda x: x['profit_ratio'])
            
            # 输出汇总信息
            self.log("="*70)
            self.log("📊 [浮盈汇总] 持仓 {} 只股票 | 总市值: ¥{:,.2f} | 总盈亏: ¥{:+,.2f}".format(
                len(positions), 
                total_market_value, 
                total_profit_amount
            ))
            self.log("="*70)
            
            # 输出盈利股票（前5只）
            if profit_stocks:
                self.log("✅ 盈利股票 (共{}只)".format(len(profit_stocks)))
                for i, stock in enumerate(profit_stocks[:5]):
                    t1_status = "可卖" if stock['can_sell'] > 0 else "T+1"
                    self.log("   📈 {} {:>+7.2f}% (现价:{:.2f} 成本:{:.2f}) [{}]".format(
                        stock['code'],
                        stock['profit_ratio'] * 100,
                        stock['current_price'],
                        stock['open_price'],
                        t1_status
                    ))
                if len(profit_stocks) > 5:
                    self.log("   ... 还有 {} 只盈利股票".format(len(profit_stocks) - 5))
            
            # 输出亏损股票（前5只）
            if loss_stocks:
                self.log("❌ 亏损股票 (共{}只)".format(len(loss_stocks)))
                for i, stock in enumerate(loss_stocks[:5]):
                    t1_status = "可卖" if stock['can_sell'] > 0 else "T+1"
                    self.log("   📉 {} {:>+7.2f}% (现价:{:.2f} 成本:{:.2f}) [{}]".format(
                        stock['code'],
                        stock['profit_ratio'] * 100,
                        stock['current_price'],
                        stock['open_price'],
                        t1_status
                    ))
                if len(loss_stocks) > 5:
                    self.log("   ... 还有 {} 只亏损股票".format(len(loss_stocks) - 5))
            
            self.log("="*70)
            
        except Exception as e:
            self.log("[警告] 浮盈汇总异常: {}".format(e))
