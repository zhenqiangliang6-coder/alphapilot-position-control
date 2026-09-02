# -*- coding: utf-8 -*-
"""
动态止盈模块 - 完全独立的三级止盈策略（分板块差异化）

功能说明：
1. 第一级（快速止盈）：所有股票上涨 3% 后回落 1.3% 立即卖出
   - 60/00开头（主板）：涨幅区间 3% ~ 8.5%
   - 68/30开头（科创/创业）：涨幅区间 3% ~ 17%
2. 第二级（波段止盈）：60/00 开头股票上涨 9% 后 12 分钟卖出
3. 第三级（强势股止盈）：68/30 开头股票上涨 18% 后 12 分钟卖出

设计原则：
- 完全独立于买入策略和其他卖出策略
- 通过独立定时器在后台运行
- 止盈卖出不影响其他策略的买入逻辑
- 【新增】第一级止盈根据板块类型使用不同的涨幅上限

【重要】时间控制：
- 为避免开盘剧烈波动导致误触发，动态止盈仅在配置时间之后执行
- 默认 09:51，可通过 config/settings.py 中的 TAKE_PROFIT_EARLIEST_TIME 调整

【配置参数】（在 config/settings.py 中修改）：
- TAKE_PROFIT_EARLIEST_TIME: 最早执行时间（默认 "0951"）
- TAKE_PROFIT_LEVEL1_GAIN_THRESHOLD: 第一级涨幅阈值（默认 3%）
- TAKE_PROFIT_LEVEL1_GAIN_MAX: 第一级涨幅上限-主板（默认 8.5%）
- TAKE_PROFIT_LEVEL1_DROP_THRESHOLD: 第一级回落阈值（默认 1.3%）
- TAKE_PROFIT_LEVEL2_GAIN_THRESHOLD: 第二级涨幅阈值（默认 9%）
- TAKE_PROFIT_LEVEL2_HOLD_MINUTES: 第二级持有时间（默认 12 分钟）
- TAKE_PROFIT_LEVEL3_GAIN_THRESHOLD: 第三级涨幅阈值（默认 18%）
- TAKE_PROFIT_LEVEL3_HOLD_MINUTES: 第三级持有时间（默认 12 分钟）
"""
import time
import datetime
import threading
from config import settings
from utils.logger import get_logger

class DynamicTakeProfit:
    def __init__(self, engine):
        self.engine = engine
        
        # 记录每只股票的止盈状态
        # 格式: {code: {
        #     'highest_profit': 0.0,      # 最高涨幅
        #     'peak_time': 0,             # 首次达到峰值的时间戳
        #     'triggered_level1': False,  # 是否已触发第一级
        #     'triggered_level2': False,  # 是否已触发第二级
        #     'triggered_level3': False   # 是否已触发第三级
        # }}
        self.profit_tracker = {}
        self.lock = threading.Lock()
        
        # 【配置化管理】从 settings 读取止盈参数（与止损模块保持一致）
        # 第一级：所有股票
        self.level1_gain_threshold = settings.TAKE_PROFIT_LEVEL1_GAIN_THRESHOLD
        self.level1_gain_max = settings.TAKE_PROFIT_LEVEL1_GAIN_MAX
        self.level1_drop_threshold = settings.TAKE_PROFIT_LEVEL1_DROP_THRESHOLD
        
        # 第二级：60/00 开头股票
        self.level2_gain_threshold = settings.TAKE_PROFIT_LEVEL2_GAIN_THRESHOLD
        self.level2_hold_minutes = settings.TAKE_PROFIT_LEVEL2_HOLD_MINUTES
        
        # 第三级：68/30 开头股票
        self.level3_gain_threshold = settings.TAKE_PROFIT_LEVEL3_GAIN_THRESHOLD
        self.level3_hold_minutes = settings.TAKE_PROFIT_LEVEL3_HOLD_MINUTES
        
        # 【配置化管理】动态止盈最早执行时间
        self.EARLIEST_EXECUTION_TIME = settings.TAKE_PROFIT_EARLIEST_TIME

    def _can_execute_now(self):
        """
        检查当前时间是否允许执行动态止盈
        
        返回：True=可以执行，False=未到执行时间
        
        【实盘修改指南】：
        - 如果想让动态止盈在 9:30 开盘后立即生效，将 EARLIEST_EXECUTION_TIME 改为 "0930"
        - 如果想延迟到 10:00 再执行，将 EARLIEST_EXECUTION_TIME 改为 "1000"
        - 如果想去掉时间限制（全天执行），直接返回 True
        """
        now = datetime.datetime.now()
        current_time = now.strftime("%H%M")
        
        # 判断当前时间是否早于最早执行时间
        if current_time < self.EARLIEST_EXECUTION_TIME:
            return False
        
        return True

    def check(self):
        """
        定期检查持仓，执行动态止盈
        
        调用时机：在主循环中定期调用（建议每 10-15 秒一次）
        
        【重要】时间过滤：
        - 仅在 EARLIEST_EXECUTION_TIME 之后执行（默认 09:35）
        - 避免开盘前5分钟剧烈波动导致误触发
        """
        log = get_logger()
        
        # 【强制日志】每次调用都输出，方便调试（与止损模块保持一致）
        now = datetime.datetime.now()
        now_time = now.strftime("%H%M")
        
        log.log("[止盈检查] 开始执行 (当前时间:{}, 最早执行:{})".format(
            now.strftime("%H:%M:%S"),
            self.EARLIEST_EXECUTION_TIME[:2] + ":" + self.EARLIEST_EXECUTION_TIME[2:]
        ))
        
        # 【时间检查】未到执行时间，直接跳过
        if not self._can_execute_now():
            log.log("[止盈跳过] 当前时间 {} 早于最早执行时间 {}，暂不执行".format(
                now.strftime("%H:%M"), 
                self.EARLIEST_EXECUTION_TIME[:2] + ":" + self.EARLIEST_EXECUTION_TIME[2:]
            ))
            return
        
        positions = self.engine.query_positions()
        
        if not positions:
            log.log("[止盈检查] 当前无持仓，跳过")
            return
        
        log.log("[止盈检查] 发现 {} 只持仓股票，开始检查...".format(len(positions)))
        
        for pos in positions:
            if pos.volume <= 0:
                continue
            
            code = pos.stock_code
            volume = pos.volume
            
            # 【关键修复】兼容多种成本价字段名（与止损模块保持一致）
            # 掘金API可能返回: open_price, cost_price, avg_price
            open_price = getattr(pos, 'open_price', 0.0)
            if open_price <= 0:
                open_price = getattr(pos, 'cost_price', 0.0)
            if open_price <= 0:
                open_price = getattr(pos, 'avg_price', 0.0)
            
            if open_price <= 0:
                log.log("[止盈跳过] {} 成本价为0，跳过".format(code))
                continue
            
            # 获取最新价格
            try:
                latest_prices = self.engine.get_latest_prices([code])
                current_price = latest_prices.get(code)
                
                if current_price is None or current_price <= 0:
                    current_price = open_price
            except Exception as e:
                log.log("[止盈] 获取 {} 行情失败: {}".format(code, e))
                continue
            
            # 计算当前盈亏比例
            profit_ratio = (current_price - open_price) / open_price
            
            # 强制输出每只股票的盈亏情况（方便调试，与止损模块保持一致）
            log.log("[止盈分析] {} 成本:{:.2f} 现价:{:.2f} 盈亏:{:.2f}%".format(
                code, open_price, current_price, profit_ratio*100
            ))
            
            # 更新止盈追踪状态
            self._update_tracker(code, profit_ratio)
            
            # 检查各级止盈条件
            self._check_level1(code, current_price, open_price, volume, profit_ratio)
            self._check_level2(code, current_price, open_price, volume, profit_ratio)
            self._check_level3(code, current_price, open_price, volume, profit_ratio)
        
        log.log("[止盈总结] 本轮未触发任何止盈")

    def _update_tracker(self, code, current_profit):
        """更新股票的最高涨幅记录"""
        # 【专家级修复】如果当前时间还没到最早执行时间，不记录峰值时间
        # 防止开盘前的剧烈波动导致计时器提前启动
        if not self._can_execute_now():
            return

        log = get_logger()
        
        with self.lock:
            if code not in self.profit_tracker:
                self.profit_tracker[code] = {
                    'highest_profit': current_profit,
                    'peak_time': time.time(),
                    'triggered_level1': False,
                    'triggered_level2': False,
                    'triggered_level3': False
                }
                log.log("[止盈初始化] {} 加入追踪器 (当前盈亏:{:.2f}%)".format(code, current_profit*100))
            else:
                # 如果当前涨幅创新高，更新时间戳
                if current_profit > self.profit_tracker[code]['highest_profit']:
                    old_highest = self.profit_tracker[code]['highest_profit']
                    self.profit_tracker[code]['highest_profit'] = current_profit
                    self.profit_tracker[code]['peak_time'] = time.time()
                    log.log("[止盈更新] {} 创新高 (旧:{:.2f}% → 新:{:.2f}%)".format(
                        code, old_highest*100, current_profit*100))

    def _check_level1(self, code, current_price, open_price, volume, profit_ratio):
        """
        第一级止盈：所有股票上涨 3% 后回落 1.3% 立即卖出
        
        【分板块差异化】
        - 60/00开头（主板）：涨幅区间 3% ~ 8.5%，回落 1.3% 卖出
        - 68/30开头（科创/创业）：涨幅区间 3% ~ 17%，回落 1.3% 卖出
        
        逻辑：
        1. 最高涨幅在有效区间内（根据板块不同）
        2. 当前涨幅 <= 最高涨幅 - 1.3%
        3. 尚未触发过第一级止盈
        4. 【A股T+1修复】必须检查可卖数量 > 0
        """
        log = get_logger()
        
        with self.lock:
            if code not in self.profit_tracker:
                return
            
            tracker = self.profit_tracker[code]
            highest = tracker['highest_profit']
            
            # 检查是否已触发
            if tracker['triggered_level1']:
                return
            
            # 【分板块差异化】确定涨幅上限
            # 提取股票代码前缀
            if '.' in code:
                numeric_part = code.split('.')[1]
                code_prefix = numeric_part[:2]
            else:
                code_prefix = code[:2]
            
            # 根据板块设置不同的涨幅上限
            if code_prefix in ['68', '30']:
                # 科创板/创业板：上限 17%
                level1_max = 0.17
                board_name = "科创/创业"
            else:
                # 主板（60/00）：使用配置的上限（默认 8.5%）
                level1_max = self.level1_gain_max
                board_name = "主板"
            
            # 【新增】检查涨幅是否在有效范围内
            if highest > level1_max:
                # 涨幅超过上限，不执行第一级止盈，交由第二/三级处理
                log.log("[止盈跳过] {} ({}) 最高涨幅{:.2f}% > 上限{:.2f}%，不执行第一级止盈（交由第二/三级处理）".format(
                    code, board_name, highest*100, level1_max*100))
                return
            
            # 判断条件：最高涨过 3%，且当前回落了 1.3%
            if highest >= self.level1_gain_threshold:
                drop_from_peak = highest - profit_ratio
                if drop_from_peak >= self.level1_drop_threshold:
                    # 【A股T+1修复】查询实际可卖数量
                    positions = self.engine.query_positions()
                    can_sell = 0
                    total_volume = 0
                    for pos in positions:
                        if pos.stock_code == code and pos.volume > 0:
                            can_sell = pos.can_use_volume
                            total_volume = pos.volume
                            break
                    
                    if can_sell <= 0:
                        log.log("[止盈跳过] {} 今日买入不可卖（总持仓:{} 可卖:0），无法执行快速止盈".format(code, total_volume))
                        return
                    
                    log.log("[止盈-快速] {} ({}) 触发第一级止盈 (最高涨幅: {:.2f}%, 当前涨幅: {:.2f}%, 回落: {:.2f}%, 可卖:{})".format(
                        code, board_name, highest * 100, profit_ratio * 100, drop_from_peak * 100, can_sell))
                    
                    # 执行卖出（使用可卖数量）
                    if self._execute_sell(code, can_sell, current_price, "止盈-快速(3%回落1.3%)"):
                        tracker['triggered_level1'] = True
                        log.log("[止盈] {} 第一级止盈完成，从追踪列表移除".format(code))
                else:
                    # 负向日志：回落幅度不足
                    log.log("[止盈跳过] {} ({}) 最高涨幅{:.2f}% >= 3%但回落{:.2f}% < 1.3%，未触发第一级止盈".format(
                        code, board_name, highest*100, drop_from_peak*100))
            else:
                # 负向日志：未达到3%阈值
                log.log("[止盈跳过] {} ({}) 最高涨幅{:.2f}% < 3%，未进入第一级止盈监控".format(
                    code, board_name, highest*100))

    def _check_level2(self, code, current_price, open_price, volume, profit_ratio):
        """
        第二级止盈：60/00 开头股票上涨 9% 后 12 分钟卖出
        
        逻辑：
        1. 股票代码以 60 或 00 开头
        2. 当前涨幅 >= 9%
        3. 距离首次达到 9% 已过 12 分钟
        4. 【A股T+1修复】必须检查可卖数量 > 0
        """
        log = get_logger()
        
        # 【关键修复】提取股票代码的数字部分前两位
        # 代码格式: SHSE.600xxx / SZSE.000xxx / SHSE.688xxx
        # 需要提取 "." 后面的数字部分的前两位
        if '.' in code:
            numeric_part = code.split('.')[1]  # 获取 "600xxx" 或 "000xxx"
            code_prefix = numeric_part[:2]     # 获取 "60" 或 "00"
        else:
            code_prefix = code[:2]             # 兼容不带交易所前缀的代码
        
        if code_prefix not in ['60', '00']:
            # 负向日志：代码前缀不匹配
            log.log("[止盈跳过] {} 代码前缀{}不属于60/00开头，不执行第二级止盈".format(code, code_prefix))
            return
        
        with self.lock:
            if code not in self.profit_tracker:
                return
            
            tracker = self.profit_tracker[code]
            
            # 检查是否已触发
            if tracker['triggered_level2']:
                return
            
            # 判断是否达到涨幅阈值
            if profit_ratio >= self.level2_gain_threshold:
                # 【修复】如果之前未达到过阈值，或回落后重新达到，重置计时器
                if tracker['peak_time'] == 0 or tracker['highest_profit'] < self.level2_gain_threshold:
                    tracker['peak_time'] = time.time()
                    tracker['highest_profit'] = max(tracker['highest_profit'], profit_ratio)
                    log.log("[止盈-波段] {} 首次达到第二级阈值 (涨幅: {:.2f}%)，开始计时 12 分钟".format(
                        code, profit_ratio * 100))
                    return
                
                # 更新最高涨幅（但不重置时间）
                tracker['highest_profit'] = max(tracker['highest_profit'], profit_ratio)
                
                # 计算持有时间
                hold_seconds = time.time() - tracker['peak_time']
                hold_minutes = hold_seconds / 60.0
                
                if hold_minutes >= self.level2_hold_minutes:
                    # 【A股T+1修复】查询实际可卖数量
                    positions = self.engine.query_positions()
                    can_sell = 0
                    total_volume = 0
                    for pos in positions:
                        if pos.stock_code == code and pos.volume > 0:
                            can_sell = pos.can_use_volume
                            total_volume = pos.volume
                            break
                    
                    if can_sell <= 0:
                        log.log("[止盈跳过] {} 今日买入不可卖（总持仓:{} 可卖:0），无法执行波段止盈".format(code, total_volume))
                        return
                    
                    log.log("[止盈-波段] {} 触发第二级止盈 (涨幅: {:.2f}%, 持有时间: {:.1f} 分钟, 可卖:{})".format(
                        code, profit_ratio * 100, hold_minutes, can_sell))
                    
                    # 执行卖出（使用可卖数量）
                    if self._execute_sell(code, can_sell, current_price, "止盈-波段(9%持有12分钟)"):
                        tracker['triggered_level2'] = True
                        log.log("[止盈] {} 第二级止盈完成，从追踪列表移除".format(code))
                else:
                    # 负向日志：持有时间不足
                    log.log("[止盈跳过] {} 涨幅{:.2f}% >= 9%但持有时间{:.1f}分钟 < 12分钟，未触发第二级止盈".format(
                        code, profit_ratio*100, hold_minutes))
            else:
                # 负向日志：未达到9%阈值
                log.log("[止盈跳过] {} 涨幅{:.2f}% < 9%，未进入第二级止盈监控".format(
                    code, profit_ratio*100))

    def _check_level3(self, code, current_price, open_price, volume, profit_ratio):
        """
        第三级止盈：68/30 开头股票上涨 18% 后 12 分钟卖出
        
        逻辑：
        1. 股票代码以 68 或 30 开头（科创板/创业板）
        2. 当前涨幅 >= 18%
        3. 距离首次达到 18% 已过 12 分钟
        4. 【A股T+1修复】必须检查可卖数量 > 0
        """
        log = get_logger()
        
        # 【关键修复】提取股票代码的数字部分前两位
        # 代码格式: SHSE.600xxx / SZSE.300xxx / SHSE.688xxx
        # 需要提取 "." 后面的数字部分的前两位
        if '.' in code:
            numeric_part = code.split('.')[1]  # 获取 "600xxx" 或 "300xxx"
            code_prefix = numeric_part[:2]     # 获取 "60" 或 "30"
        else:
            code_prefix = code[:2]             # 兼容不带交易所前缀的代码
        
        if code_prefix not in ['68', '30']:
            # 负向日志：代码前缀不匹配
            log.log("[止盈跳过] {} 代码前缀{}不属于68/30开头，不执行第三级止盈".format(code, code_prefix))
            return

        with self.lock:
            if code not in self.profit_tracker:
                return
            
            tracker = self.profit_tracker[code]
            
            # 检查是否已触发
            if tracker['triggered_level3']:
                return
            
            # 判断是否达到涨幅阈值
            if profit_ratio >= self.level3_gain_threshold:
                # 【修复】如果之前未达到过阈值，或回落后重新达到，重置计时器
                if tracker['peak_time'] == 0 or tracker['highest_profit'] < self.level3_gain_threshold:
                    tracker['peak_time'] = time.time()
                    tracker['highest_profit'] = max(tracker['highest_profit'], profit_ratio)
                    log.log("[止盈-强势] {} 首次达到第三级阈值 (涨幅: {:.2f}%)，开始计时 12 分钟".format(
                        code, profit_ratio * 100))
                    return
                
                # 更新最高涨幅（但不重置时间）
                tracker['highest_profit'] = max(tracker['highest_profit'], profit_ratio)
                
                # 计算持有时间
                hold_seconds = time.time() - tracker['peak_time']
                hold_minutes = hold_seconds / 60.0
                
                if hold_minutes >= self.level3_hold_minutes:
                    # 【A股T+1修复】查询实际可卖数量
                    positions = self.engine.query_positions()
                    can_sell = 0
                    total_volume = 0
                    for pos in positions:
                        if pos.stock_code == code and pos.volume > 0:
                            can_sell = pos.can_use_volume
                            total_volume = pos.volume
                            break
                    
                    if can_sell <= 0:
                        log.log("[止盈跳过] {} 今日买入不可卖（总持仓:{} 可卖:0），无法执行强势止盈".format(code, total_volume))
                        return
                    
                    log.log("[止盈-强势] {} 触发第三级止盈 (涨幅: {:.2f}%, 持有时间: {:.1f} 分钟, 可卖:{})".format(
                        code, profit_ratio * 100, hold_minutes, can_sell))
                    
                    # 执行卖出（使用可卖数量）
                    if self._execute_sell(code, can_sell, current_price, "止盈-强势(18%持有12分钟)"):
                        tracker['triggered_level3'] = True
                        log.log("[止盈] {} 第三级止盈完成，从追踪列表移除".format(code))
                else:
                    # 负向日志：持有时间不足
                    log.log("[止盈跳过] {} 涨幅{:.2f}% >= 18%但持有时间{:.1f}分钟 < 12分钟，未触发第三级止盈".format(
                        code, profit_ratio*100, hold_minutes))
            else:
                # 负向日志：未达到18%阈值
                log.log("[止盈跳过] {} 涨幅{:.2f}% < 18%，未进入第三级止盈监控".format(
                    code, profit_ratio*100))

    def _execute_sell(self, code, volume, current_price, reason):
        """
        执行卖出操作
        
        参数：
        - code: 股票代码
        - volume: 卖出数量
        - current_price: 当前价格
        - reason: 止盈原因（用于日志记录）
        
        返回：True 成功，False 失败
        """
        log = get_logger()
        
        # A股规则：卖出数量必须是100的整数倍
        actual_volume = (volume // 100) * 100
        
        if actual_volume <= 0:
            log.log("[止盈跳过] {} 数量不足100股，无法卖出".format(code))
            return False
        
        # 【修复】获取跌停价进行保护
        try:
            latest_prices = self.engine.get_latest_prices([code])
            current_tick = latest_prices.get(code, {})
            limit_down = current_tick.get('limitDown', 0.0) if isinstance(current_tick, dict) else 0.0
        except Exception as e:
            log.log("[止盈警告] {} 获取跌停价失败: {}".format(code, e))
            limit_down = 0.0
        
        # 卖出价格：当前价格 * 0.99（略微让利，提高成交率）
        sell_price = round(current_price * 0.99, 2)
        
        # 【新增】跌停保护：不能低于跌停价
        if limit_down > 0 and sell_price < limit_down:
            sell_price = limit_down
            log.log("[止盈] {} 使用跌停价卖出：{}".format(code, sell_price))
        
        log.log("[止盈执行] {} 卖出 {} 股 @ {} ({})".format(code, actual_volume, sell_price, reason))
        
        try:
            success = self.engine.order_stock(code, "SELL", actual_volume, sell_price, reason)
            
            if success:
                log.log("[止盈成功] {} 已卖出，原因: {}".format(code, reason))
                return True
            else:
                log.log("[止盈失败] {} 下单失败".format(code))
                return False
        except Exception as e:
            log.log("[止盈错误] {} 卖出异常: {}".format(code, e))
            return False

    def reset_tracker(self, code):
        """
        重置某只股票的止盈追踪（可选）
        
        使用场景：股票卖出后重新买入，需要重新追踪止盈
        """
        with self.lock:
            if code in self.profit_tracker:
                del self.profit_tracker[code]
