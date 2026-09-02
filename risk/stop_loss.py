# -*- coding: utf-8 -*-
"""
动态止损模块 - 掘金量化版 (V9.1)

功能说明：
1. 监控阶段：当亏损达到-0.5%时开始跟踪记录
2. 一级止损：亏损达到-1.2%时，执行50%仓位减仓
3. 二级止损：亏损达到-2.5%时，执行全部清仓
4. 反弹保护：触发一级止损后，若反弹超过成本价，重置止损状态

时间控制：
- 仅在 STOP_LOSS_START_TIME 之后执行（默认 10:45）
- 在 STOP_LOSS_END_TIME 之前结束（默认 14:50）
"""
from config import settings
from utils.logger import get_logger
import time
import threading
import datetime


class StopLossMonitor:
    def __init__(self, engine):
        self.engine = engine
        
        # 动态止损追踪器
        # 格式: {code: {
        #     'monitoring': False,           # 是否进入监控状态（-0.5%触发）
        #     'level1_triggered': False,     # 是否已触发一级止损
        #     'level1_sell_volume': 0,       # 一级止损已卖出数量
        #     'original_volume': 0,          # 原始持仓数量
        #     'open_price': 0.0,             # 开仓成本
        #     'monitor_start_time': 0,       # 开始监控的时间戳
        #     'lowest_profit': 0.0,          # 监控期间最低盈亏比例
        # }}
        self.stop_loss_tracker = {}
        self.lock = threading.Lock()

    def check(self):
        """定期检查持仓，执行动态止损
        
        【重要】时间控制：
        - 仅在 STOP_LOSS_START_TIME 之后执行（默认 10:45）
        - 在 STOP_LOSS_END_TIME 之前结束（默认 14:50）
        - 避免开盘剧烈波动导致误触发止损
        - 避开尾盘集合竞价阶段（14:50-15:00）流动性差的问题
        - 如需调整时间，请修改 config/settings.py 中的相关配置
        """
        log = get_logger()  # 动态获取
        
        # 【强制日志】每次调用都输出，方便调试
        now = datetime.datetime.now()
        now_time = now.strftime("%H%M")
        
        log.log("[止损检查] 开始执行 (当前时间:{}, 窗口:{}-{})".format(
            now.strftime("%H:%M:%S"),
            settings.STOP_LOSS_START_TIME[:2] + ":" + settings.STOP_LOSS_START_TIME[2:],
            settings.STOP_LOSS_END_TIME[:2] + ":" + settings.STOP_LOSS_END_TIME[2:]
        ))
        
        # 【时间检查】判断是否在允许的时间窗口内
        # 未到开始时间，跳过
        if now_time < settings.STOP_LOSS_START_TIME:
            log.log("[止损跳过] 当前时间 {} 早于最早执行时间 {}，暂不执行".format(
                now.strftime("%H:%M"), 
                settings.STOP_LOSS_START_TIME[:2] + ":" + settings.STOP_LOSS_START_TIME[2:]
            ))
            return
        
        # 已超过结束时间，跳过
        if now_time >= settings.STOP_LOSS_END_TIME:
            log.log("[止损跳过] 当前时间 {} 已超过最晚执行时间 {}，今日止损检查结束".format(
                now.strftime("%H:%M"), 
                settings.STOP_LOSS_END_TIME[:2] + ":" + settings.STOP_LOSS_END_TIME[2:]
            ))
            return
        
        # 查询持仓
        positions = self.engine.query_positions()
        if not positions:
            log.log("[止损检查] 当前无持仓，跳过")
            return
        
        log.log("[止损检查] 发现 {} 只持仓股票，开始检查...".format(len(positions)))
        
        stop_loss_count = 0
        
        for pos in positions:
            if pos.volume <= 0:
                continue
            
            code = pos.stock_code
            current_volume = pos.volume
            
            # 【关键修复】兼容多种成本价字段名
            # 掘金API可能返回: open_price, cost_price, avg_price
            open_price = getattr(pos, 'open_price', 0.0)
            if open_price <= 0:
                open_price = getattr(pos, 'cost_price', 0.0)
            if open_price <= 0:
                open_price = getattr(pos, 'avg_price', 0.0)
            
            if open_price <= 0:
                log.log("[止损跳过] {} 成本价为0，跳过".format(code))
                continue
            
            # 【修复】使用真正的实时行情API获取最新价格
            latest_prices = self.engine.get_latest_prices([code])
            current_price = latest_prices.get(code)
            
            if current_price is None or current_price <= 0:
                current_price = open_price
            
            # 计算当前盈亏比例
            profit_ratio = (current_price - open_price) / open_price
            loss_ratio = -profit_ratio  # 转为正数表示亏损
            
            # 强制输出每只股票的盈亏情况（方便调试）
            log.log("[止损分析] {} 成本:{:.2f} 现价:{:.2f} 盈亏:{:.2f}% 亏损:{:.2f}%".format(
                code, open_price, current_price, profit_ratio*100, loss_ratio*100
            ))
            
            # 更新或初始化追踪器
            with self.lock:
                if code not in self.stop_loss_tracker:
                    self.stop_loss_tracker[code] = {
                        'monitoring': False,
                        'level1_triggered': False,
                        'level1_sell_volume': 0,
                        'original_volume': current_volume,
                        'open_price': open_price,
                        'monitor_start_time': 0,
                        'lowest_profit': profit_ratio
                    }
                    log.log("[止损初始化] {} 加入追踪器".format(code))
                
                tracker = self.stop_loss_tracker[code]
                
                # 更新最低盈亏比例（用于追踪最大回撤）
                if profit_ratio < tracker['lowest_profit']:
                    tracker['lowest_profit'] = profit_ratio
                
                # 更新原始持仓（如果变化）
                if tracker['original_volume'] == 0:
                    tracker['original_volume'] = current_volume
            
            # 【阶段1】监控触发：亏损达到-0.5%
            if not tracker['monitoring'] and loss_ratio >= 0.005:
                with self.lock:
                    tracker['monitoring'] = True
                    tracker['monitor_start_time'] = time.time()
                log.log("[止损-监控] {} 进入监控状态 (成本:{:.2f} 现价:{:.2f} 亏损:{:.2f}%)".format(
                    code, open_price, current_price, loss_ratio*100))
            
            if not tracker['monitoring']:
                log.log("[止损跳过] {} 亏损{:.2f}% < 监控阈值0.5%，未进入监控".format(code, loss_ratio*100))
                continue
            
            # 【反弹保护】
            if tracker['level1_triggered'] and profit_ratio > 0:
                with self.lock:
                    tracker['level1_triggered'] = False
                    tracker['level1_sell_volume'] = 0
                    tracker['monitoring'] = False
                    tracker['lowest_profit'] = profit_ratio
                log.log("[止损-重置] {} 股价反弹超过成本价，止损状态重置 (当前盈利:{:.2f}%)".format(
                    code, profit_ratio*100))
                continue
            
            # 【阶段2】一级止损：亏损达到-1.2%，卖出50%仓位
            if not tracker['level1_triggered'] and loss_ratio >= 0.012:
                # 【A股T+1修复】必须使用可卖数量，而非总持仓
                sell_volume = current_volume // 2
                
                # A股规则：卖出数量必须是100的整数倍
                sell_volume = (sell_volume // 100) * 100
                
                # 检查实际可卖数量
                remaining_positions = self.engine.query_positions()
                can_sell = 0
                for p in remaining_positions:
                    if p.stock_code == code and p.volume > 0:
                        can_sell = p.can_use_volume
                        break
                
                # 实际卖出数量不能超过可卖数量
                actual_sell_volume = min(sell_volume, can_sell)
                
                if actual_sell_volume > 0:
                    log.log("[止损-一级] {} 触发一级止损 (成本:{:.2f} 现价:{:.2f} 亏损:{:.2f}% 总持仓:{} 可卖:{})".format(
                        code, open_price, current_price, loss_ratio*100, current_volume, can_sell))
                    
                    if self._execute_stop_loss(code, actual_sell_volume, current_price, "一级止损(-1.2%减半)"):
                        with self.lock:
                            tracker['level1_triggered'] = True
                            tracker['level1_sell_volume'] = actual_sell_volume
                        stop_loss_count += 1
                        log.log("[止损] {} 一级止损完成，已卖出 {} 股（可卖{}股）".format(code, actual_sell_volume, can_sell))
                    else:
                        log.log("[止损失败] {} 一级止损执行失败".format(code))
                else:
                    log.log("[止损跳过] {} 今日买入不可卖（总持仓:{} 可卖:0），无法执行一级止损".format(code, current_volume))
            
            # 【阶段3】二级止损：亏损达到-2.5%，全部清仓
            if loss_ratio >= 0.025:
                # 【A股T+1修复】检查剩余可卖数量
                remaining_positions = self.engine.query_positions()
                can_sell = 0
                for p in remaining_positions:
                    if p.stock_code == code and p.volume > 0:
                        can_sell = p.can_use_volume
                        break
                
                if can_sell > 0:
                    log.log("[止损-二级] {} 触发二级止损 (成本:{:.2f} 现价:{:.2f} 亏损:{:.2f}% 总持仓:{} 可卖:{})".format(
                        code, open_price, current_price, loss_ratio*100, current_volume, can_sell))
                    
                    if self._execute_stop_loss(code, can_sell, current_price, "二级止损(-2.5%清仓)"):
                        with self.lock:
                            # 清仓后移除追踪
                            del self.stop_loss_tracker[code]
                        stop_loss_count += 1
                        log.log("[止损] {} 二级止损完成，已清仓 {} 股（可卖{}股）".format(code, can_sell, can_sell))
                    else:
                        log.log("[止损失败] {} 二级止损执行失败".format(code))
                else:
                    log.log("[止损跳过] {} 今日买入不可卖（总持仓:{} 可卖:0），无法执行二级止损".format(code, current_volume))
        
        # 最终汇总
        if stop_loss_count > 0:
            log.log("[止损总结] 本轮共执行 {} 次止损操作".format(stop_loss_count))
        else:
            log.log("[止损总结] 本轮未触发任何止损")

    def _execute_stop_loss(self, code, volume, current_price, reason):
        """执行止损卖出
        
        参数：
        - code: 股票代码
        - volume: 卖出数量
        - current_price: 当前价格
        - reason: 止损原因（用于日志）
        
        返回：True 成功，False 失败
        """
        log = get_logger()
        
        # 检查是否有可用持仓
        positions = self.engine.query_positions()
        can_sell = 0
        for pos in positions:
            if pos.stock_code == code and pos.volume > 0:
                can_sell = pos.can_use_volume
                break
        
        if can_sell <= 0:
            log.log("[止损] {} 无可用持仓，跳过".format(code))
            return False
        
        # 实际卖出数量取较小值并确保是100的整数倍
        actual_volume = min(volume, can_sell)
        # A股规则：卖出数量必须是100的整数倍
        actual_volume = (actual_volume // 100) * 100
        
        if actual_volume <= 0:
            log.log("[止损跳过] {} 数量不足100股，无法卖出".format(code))
            return False
        
        # 跌停保护：不能低于跌停价
        latest_prices = self.engine.get_latest_prices([code])
        current_tick = latest_prices.get(code, {})
        limit_down = current_tick.get('limitDown', 0.0) if isinstance(current_tick, dict) else 0.0
        
        # 卖出价格：折价1%确保成交
        sell_price = round(current_price * 0.99, 2)
        if limit_down > 0 and sell_price < limit_down:
            sell_price = limit_down
            log.log("[止损] {} 使用跌停价卖出：{}".format(code, sell_price))
        
        # 执行卖出
        if self.engine.order_stock(code, "SELL", actual_volume, sell_price, reason):
            log.log("[止损执行] 成功卖出 {} {} 股 @ {} ({})".format(code, actual_volume, sell_price, reason))
            return True
        else:
            log.log("[止损失败] {} 下单失败".format(code))
            return False
    
    def reset_tracker(self, code):
        """
        重置某只股票的止损追踪（可选）
        
        使用场景：股票卖出后重新买入，需要重新追踪止损
        """
        with self.lock:
            if code in self.stop_loss_tracker:
                del self.stop_loss_tracker[code]
