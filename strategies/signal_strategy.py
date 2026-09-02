# -*- coding: utf-8 -*-
"""
信号驱动策略 - 掘金量化版（工业级事件驱动）
"""

import os
import json
import shutil
import time
import threading
import datetime
from config import settings
from utils.logger import get_logger
from gm.api import current


def convert_stock_code(code):
    """股票代码转换为掘金标准格式"""
    if not code or '.' not in code:
        return code
    
    parts = code.split('.')
    if parts[0] in ['SHSE', 'SZSE']:
        return code
    
    stock_num = parts[0]
    exchange = parts[1].upper()
    
    if exchange == 'SH':
        return f'SHSE.{stock_num}'
    elif exchange == 'SZ':
        return f'SZSE.{stock_num}'
    
    return code


class SignalStrategy:
    def __init__(self, engine):
        self.engine = engine
        self.order_history = {}
        self.history_lock = threading.Lock()
        self.delayed_strategy = None

    def set_delayed_strategy(self, delayed_strat):
        """注入延时策略实例"""
        self.delayed_strategy = delayed_strat

    def _get_index_change(self):
        """
        获取上证指数(SHSE.000001)相对于今日开盘价的涨跌幅
        """
        try:
            # 获取上证指数实时行情
            ticks = current(['SHSE.000001'], fields=['price', 'open'])
            if ticks and len(ticks) > 0:
                tick = ticks[0]
                price = tick.get('price', 0)
                open_price = tick.get('open', 0)
                if open_price > 0:
                    change_pct = (price - open_price) / open_price * 100
                    return round(change_pct, 2)
        except Exception:
            # 异常静默处理，由调用方统一输出警告
            pass
        return None

    # ============================================================
    # ⭐ 事件驱动入口（watchdog 调用）
    # ============================================================
    def process_single_signal(self, signal_file_path):
        log = get_logger()
        
        if not os.path.exists(signal_file_path):
            log.log(f"[警告] 信号文件不存在: {signal_file_path}")
            return
        
        filename = os.path.basename(signal_file_path)
        has_valid_action = False
        
        try:
            with open(signal_file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            # 【兼容性修复】同时支持 JSON 数组和 JSONL 格式
            signals = []
            if content.startswith('['):
                # JSON 数组格式: [{"code": "...", ...}, {...}]
                try:
                    signals = json.loads(content)
                    if not isinstance(signals, list):
                        signals = [signals]
                except Exception as e:
                    log.log(f"[解析] JSON 数组错误 {filename}: {e}")
                    return
            else:
                # JSONL 格式: 每行一个 JSON 对象
                lines = content.split('\n')
                for line in lines:
                    if not line.strip():
                        continue
                    try:
                        sig = json.loads(line)
                        signals.append(sig)
                    except Exception as e:
                        log.log(f"[解析] JSONL 行错误 {filename}: {e}")
            
            # 处理所有信号
            for sig in signals:
                try:
                    code = convert_stock_code(sig.get('code'))
                    action = sig.get('action') or sig.get('signal')  # 兼容 action/signal 字段
                    price = float(sig.get('price', 0) or sig.get('current_price', 0))  # 兼容 price/current_price
                    vr = float(sig.get('volume_ratio', 0))
                    
                    if not code or not action:
                        continue
                    
                    has_valid_action = True
                    
                    # ============================
                    # SELL 信号直接执行
                    # ============================
                    if action == "SELL":
                        self._execute_signal(code, action, price, vr)
                        continue
                    
                    # ============================
                    # 执行信号 (BUY/SELL)
                    # ============================
                    self._execute_signal(code, action, price, vr)
                
                except Exception as e:
                    log.log(f"[解析] 信号处理错误 {filename}: {e}")
            
            # 归档文件
            dest = os.path.join(settings.SIGNAL_DIR_PROCESSED, filename)
            if os.path.exists(dest):
                dest = os.path.join(settings.SIGNAL_DIR_PROCESSED, f"{int(time.time())}_{filename}")
            shutil.move(signal_file_path, dest)
            
            # 【修复】增加明确的归档日志，即使没有符合条件的个股也能看到文件被处理了
            if has_valid_action:
                log.log(f"[归档] {filename} -> processed (包含有效信号)")
            else:
                log.log(f"[归档] {filename} -> processed (无有效信号内容)")
        
        except Exception as e:
            log.log(f"[错误] 处理文件 {filename} 失败: {e}")

    # ============================================================
    # ⭐ 传统扫描模式（兼容）
    # ============================================================
    def process_files(self):
        log = get_logger()
        
        if not os.path.exists(settings.SIGNAL_DIR_INPUT):
            return
        
        try:
            files = [f for f in os.listdir(settings.SIGNAL_DIR_INPUT) if f.endswith(".txt")]
        except Exception as e:
            log.log(f"[错误] 读取信号目录失败: {e}")
            return
        
        for filename in sorted(files):
            self.process_single_signal(os.path.join(settings.SIGNAL_DIR_INPUT, filename))

    # ============================================================
    # ⭐ 执行立即策略（BUY/SELL）
    # ============================================================
    def _execute_signal(self, code, action, price, vr):
        log = get_logger()
        
        # 【探照灯】明确记录开始处理该信号
        log.log(f"[立即策略-启动] {code} {action} | 价格:{price} | 量比:{vr}")
        
        # ⭐ 核心修复：SELL信号跳过重复保护，但保留大盘和量比检查（防止卖飞）
        if action == "SELL":
            log.log(f"[卖出优先] {code} 卖出信号，跳过重复保护，执行大盘/量比检查")
            
            # 1. 检查大盘和量比（防止卖飞）
            if not self._decide_action(action, vr):
                log.log(f"[卖出拦截] {code} 未通过大盘/量比过滤，暂不卖出（防止卖飞）")
                return False
            
            # 2. 检查持仓（不检查重复保护）
            positions = self.engine.query_positions()
            hold_map = {p.stock_code: p for p in positions if p.volume > 0}
            
            if code not in hold_map:
                log.log(f"[卖出失败] {code} 无持仓，跳过")
                return False
            
            pos = hold_map[code]
            if pos.can_use_volume <= 0:
                log.log(f"[卖出失败] {code} 无可用持仓，跳过")
                return False
            
            # 【A股T+1修复】必须检查可卖数量并取整到100的倍数
            sell_volume = (pos.can_use_volume // 100) * 100
            
            if sell_volume <= 0:
                log.log(f"[卖出失败] {code} 无可用持仓或数量不足100股，跳过")
                return False
            
            # 3. 卖出价格：当前价打1%折扣
            order_price = round(price * 0.99, 2)
            
            # 4. 直接卖出所有可卖持仓（已取整）
            result = self.engine.order_stock(code, "SELL", sell_volume, order_price, "SIGNAL_V9")
            if result:
                log.log(f"[卖出成功] {code} 卖出 {sell_volume} 股 @ {order_price}")
            return result
        
        # ====================
        # BUY 信号：继续执行完整过滤逻辑
        # ====================
        
        # 【核心修复】先检查是否为延时股票，如果是则加入观察名单并跳过立即买入
        if self.delayed_strategy:
            should_delay = self.delayed_strategy.process_signal(code, action, price, vr)
            if should_delay:
                log.log(f"[延时策略拦截] {code} 已被加入延时观察名单，跳过立即买入")
                return True
        
        # 1. 过滤策略（集成大盘联动控制）
        if not self._decide_action(action, vr):
            log.log(f"[立即策略-终止] {code} 未通过大盘/量比过滤")
            return False
        
        # 2. 重复保护
        if not self._check_repeat_protection(code, action):
            log.log(f"[保护] {code} {action} 在保护期内，跳过")
            return False
        
        # 3. 仓位计算
        allow, vol, reason = self._check_position_and_calculate_volume(code, action, price)
        if not allow:
            log.log(f"[仓位] {code} 计算失败: {reason}")
            return False
        
        # 4. 下单
        order_price = round(price * 1.01, 2)
        result = self.engine.order_stock(code, action, vol, order_price, "SIGNAL_V9")
        if result:
            log.log(f"[立即策略-成功] {code} 订单已提交")
        return result

    # ============================================================
    # ⭐ BUY/SELL 过滤逻辑（含大盘联动与时段区分）
    # ============================================================
    def _decide_action(self, action, vr):
        """
        【顶级量化策略】分时段量比阈值控制
        
        核心逻辑：
        - 基础量比序列：1.5 → 2.25(×1.5) → 3.375(×1.5) → 5.06(×1.5)
        - 大盘向上（-0.35% ~ 1.9%）：使用基础量比
        - 大盘向下（-1.0% ~ -0.35%）：基础量比 × 1.5
        
        时段划分：
        - 09:30-10:30: 基础量比 1.5
        - 10:30-11:30: 基础量比 2.25
        - 13:00-14:00: 基础量比 3.375
        - 14:00-15:00: 基础量比 5.06
        """
        log = get_logger()
        index_change = self._get_index_change()
        
        # 【调试】打印大盘状态
        if index_change is not None:
            log.log(f"[大盘监控] 上证指数涨跌幅: {index_change:.2f}%")
        else:
            log.log(f"[大盘监控] 无法获取上证指数数据（可能是非交易时间或API延迟），禁止交易")
            return False

        # 获取当前时间，判断具体时段
        now = datetime.datetime.now()
        time_str = now.strftime("%H%M")
        
        # 细分四个时段
        is_morning_early = ("0930" <= time_str < "1030")   # 09:30-10:30
        is_morning_late = ("1030" <= time_str <= "1130")   # 10:30-11:30
        is_afternoon_early = ("1300" <= time_str < "1400") # 13:00-14:00
        is_afternoon_late = ("1400" <= time_str <= "1500") # 14:00-15:00
        
        period_name = ""
        if is_morning_early:
            period_name = "上午早盘(09:30-10:30)"
        elif is_morning_late:
            period_name = "上午尾盘(10:30-11:30)"
        elif is_afternoon_early:
            period_name = "下午早盘(13:00-14:00)"
        elif is_afternoon_late:
            period_name = "下午尾盘(14:00-15:00)"
        else:
            period_name = "非交易时段"

        # ==================== 买入策略 ====================
        if action == "BUY":
            # 定义基础量比序列（大盘向上时使用）
            base_vr_map = {
                'morning_early': 1.5,      # 09:30-10:30
                'morning_late': 2.25,      # 10:30-11:30 (1.5 × 1.5)
                'afternoon_early': 3.375,  # 13:00-14:00 (2.25 × 1.5)
                'afternoon_late': 5.06     # 14:00-15:00 (3.375 × 1.5)
            }
            
            # 根据时段获取基础量比
            if is_morning_early:
                base_vr = base_vr_map['morning_early']
            elif is_morning_late:
                base_vr = base_vr_map['morning_late']
            elif is_afternoon_early:
                base_vr = base_vr_map['afternoon_early']
            elif is_afternoon_late:
                base_vr = base_vr_map['afternoon_late']
            else:
                log.log(f"[买入拦截] {period_name} 非交易时段")
                return False
            
            # 判断大盘区间并计算最终阈值
            # 规则1: 大盘在 -0.30% 至 1.9% 之间（正常区间）
            if -0.30 <= index_change <= 1.9:
                threshold = base_vr
                market_status = "正常"
            
            # 规则2: 大盘在 -1.0% 至 -0.30% 之间（弱势区间）
            elif -1.0 <= index_change < -0.30:
                threshold = base_vr * 1.5  # 弱势时量比要求提高50%
                market_status = "弱势"
            
            # 其他情况：超出安全区间
            else:
                log.log(f"[买入拦截] {period_name} | 大盘{index_change:.2f}% 超出安全区间 [-1.0%, 1.9%]")
                return False
            
            # 判断是否通过
            if vr >= threshold:
                log.log(f"[买入通过] {period_name} | 大盘{market_status}{index_change:.2f}% | 量比{vr:.2f} >= 阈值{threshold:.2f}")
                return True
            else:
                log.log(f"[买入拦截] {period_name} | 大盘{market_status}{index_change:.2f}% | 量比{vr:.2f} < 阈值{threshold:.2f}")
                return False

        # ==================== 卖出策略 ====================
        else:  # action == "SELL"
            # 规则1: 大盘在 -0.30% 至 1.9% 之间（正常区间）
            if -0.30 <= index_change <= 1.9:
                threshold = 1.5
                if vr >= threshold:
                    log.log(f"[卖出通过] 大盘正常{index_change:.2f}% | 量比{vr:.2f} >= {threshold}")
                    return True
                else:
                    log.log(f"[卖出拦截] 大盘正常{index_change:.2f}% | 量比{vr:.2f} < {threshold}")
                    return False
            
            # 规则2: 大盘在 -1.0% 至 -0.30% 之间（弱势区间）
            elif -1.0 <= index_change < -0.30:
                threshold = 1.0
                if vr >= threshold:
                    log.log(f"[卖出通过](弱势) 大盘{index_change:.2f}% | 量比{vr:.2f} >= {threshold}")
                    return True
                else:
                    log.log(f"[卖出拦截](弱势) 大盘{index_change:.2f}% | 量比{vr:.2f} < {threshold}")
                    return False
            
            # 其他情况：超出策略区间
            else:
                log.log(f"[卖出拦截] 大盘{index_change:.2f}% 超出策略区间 [-1.0%, 1.9%]")
                return False

    # ============================================================
    # ⭐ 重复保护
    # ============================================================
    def _check_repeat_protection(self, code, action):
        key = f"{code}_{action}"
        now = time.time()
        
        with self.history_lock:
            if key in self.order_history and now - self.order_history[key] < settings.REPEAT_PROTECT_SECONDS:
                return False
            
            self.order_history[key] = now
            return True

    # ============================================================
    # ⭐ 仓位计算（掘金量化版）
    # ============================================================
    def _check_position_and_calculate_volume(self, code, action, price):
        """
        检查持仓并计算买入/卖出数量
        """
        log = get_logger()
            
        if action == "SELL":
            positions = self.engine.query_positions()
            pos = next((p for p in positions if p.stock_code == code), None)
            if not pos or pos.can_use_volume <= 0:
                return False, 0, "无可卖持仓"
            # A股规则：卖出数量必须是100的整数倍
            sell_volume = (pos.can_use_volume // 100) * 100
            if sell_volume <= 0:
                return False, 0, "可卖数量不足100股"
            return True, sell_volume, "卖出全部可用(已取整)"
            
        # BUY 逻辑
        asset = self.engine.query_asset()
        if not asset:
            return False, 0, "资产查询失败"
            
        available_cash = asset.get('cash', 0)
        if available_cash <= 0:
            return False, 0, "可用资金不足"
            
        # 资金管理：单笔使用可用资金的 80%
        SINGLE_ORDER_CASH_RATIO = 0.8
        order_value = available_cash * SINGLE_ORDER_CASH_RATIO
            
        # 限制单笔最大金额（例如 50000 元）
        MAX_SINGLE_ORDER_VALUE = 50000
        order_value = min(order_value, MAX_SINGLE_ORDER_VALUE)
            
        if price <= 0:
            return False, 0, "价格无效"
                
        volume = int(order_value / price / 100) * 100
            
        if volume < 100:
            return False, 0, f"计算股数不足100股 (资金:{available_cash:.2f})"
            
        log.log(f"[仓位计算] {code} 计划买入 {volume} 股 (约 {volume * price:.2f} 元)")
        return True, volume, "计算成功"