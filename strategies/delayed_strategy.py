# -*- coding: utf-8 -*-
"""
延时策略 - 掘金量化版
Alphapilot智能体团队
作者: 梁子羿、侯沣睿、梁茹真
邮箱: 497720537@qq.com | 电话: 13392077558

版本说明: V9.0 - 基于掘金平台
"""
import os
import json
import datetime
from utils.logger import get_logger
from config import settings


class DelayedStrategy:
    def __init__(self, engine):
        self.engine = engine
        
        # 路径配置
        self.personalities_file = os.path.join(settings.DATA_DIR, "stock_personalities.json")
        self.watchlist_file = os.path.join(settings.DATA_DIR, "delayed_watchlist.json")
        
        # 加载配置
        self.stock_personalities = self._load_personalities()
        self.delayed_watchlist = self._load_watchlist()

    def _load_personalities(self):
        logger = get_logger()
        if not os.path.exists(self.personalities_file):
            if logger:
                logger.log(f"[错误] 配置文件不存在: {self.personalities_file}")
            return {}
        try:
            with open(self.personalities_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if logger:
                logger.log(f"[成功] 加载股票个性配置: {len(data)}只股票")
                # 【调试】输出600821的配置
                if '600821' in data:
                    logger.log(f"[调试] 600821配置: type={data['600821'].get('type')}")
                else:
                    logger.log(f"[警告] 配置文件中未找到600821")
            return data
        except Exception as e:
            if logger:
                logger.log(f"[错误] 读取配置文件失败: {e}")
            return {}

    def _load_watchlist(self):
        logger = get_logger()
        if not os.path.exists(self.watchlist_file):
            empty_list = {"last_update": "", "watchlist": {}}
            self._save_watchlist(empty_list)
            return empty_list
        try:
            with open(self.watchlist_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except Exception as e:
            if logger:
                logger.log(f"[警告] 加载观察名单失败: {e}")
            return {"last_update": "", "watchlist": {}}

    def _save_watchlist(self, data=None):
        logger = get_logger()
        if data is None:
            data = self.delayed_watchlist
            
        data['last_update'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            with open(self.watchlist_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            if logger:
                logger.log(f"[保存] 观察名单已更新: {len(data.get('watchlist', {}))}只")
        except Exception as e:
            if logger:
                logger.log(f"[错误] 保存观察名单失败: {e}")

    # ============================================================
    # ⭐ 核心方法：从Alphapilot信号文件中获取最新量比
    # ============================================================
    def _get_latest_signal_volume_ratio(self, code):
        """
        从Alphapilot智能体发送的信号文件中读取指定股票的最新量比
        
        参数:
            code: 股票代码 (如 SHSE.600821 或 SZSE.001309)
        
        返回:
            float: 最新量比值，如果未找到则返回 None
        
        搜索策略:
        1. 优先搜索 signals/ 目录下的未处理信号文件
        2. 其次搜索 signals/processed/ 目录下今日的信号文件
        3. 按时间戳排序，返回最新的信号中的量比
        """
        logger = get_logger()
        
        # 提取纯数字代码用于匹配
        pure_code = code.split('.')[-1] if '.' in code else code
        
        latest_signal = None
        latest_time = None
        
        # 搜索目录列表（优先级从高到低）
        search_dirs = [
            settings.SIGNAL_DIR_INPUT,          # 未处理信号
            settings.SIGNAL_DIR_PROCESSED,      # 已处理信号
        ]
        
        for search_dir in search_dirs:
            if not os.path.exists(search_dir):
                continue
            
            try:
                # 遍历所有.txt信号文件
                for filename in os.listdir(search_dir):
                    if not filename.endswith('.txt'):
                        continue
                    
                    filepath = os.path.join(search_dir, filename)
                    
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read().strip()
                        
                        # 支持JSON数组和JSONL格式
                        signals = []
                        if content.startswith('['):
                            # JSON数组格式
                            try:
                                signals = json.loads(content)
                                if not isinstance(signals, list):
                                    signals = [signals]
                            except:
                                continue
                        else:
                            # JSONL格式
                            for line in content.split('\n'):
                                if not line.strip():
                                    continue
                                try:
                                    sig = json.loads(line)
                                    signals.append(sig)
                                except:
                                    continue
                        
                        # 查找匹配的股票信号
                        for sig in signals:
                            sig_code = sig.get('code', '')
                            # 提取纯数字代码进行匹配
                            sig_pure_code = sig_code.split('.')[-1] if '.' in sig_code else sig_code
                            
                            if sig_pure_code == pure_code and sig.get('action') == 'BUY':
                                # 提取时间戳
                                ts_str = sig.get('ts', '')
                                if ts_str:
                                    try:
                                        ts = datetime.datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S')
                                        if latest_time is None or ts > latest_time:
                                            latest_time = ts
                                            latest_signal = sig
                                    except:
                                        pass
                    except Exception as e:
                        if logger:
                            logger.log(f"[警告] 读取信号文件 {filename} 失败: {e}")
            
            except Exception as e:
                if logger:
                    logger.log(f"[警告] 扫描目录 {search_dir} 失败: {e}")
        
        # 返回最新信号中的量比
        if latest_signal:
            volume_ratio = latest_signal.get('volume_ratio', 0)
            if logger:
                logger.log(f"[信号查询] {code} 最新量比: {volume_ratio:.2f} (时间: {latest_time})")
            return volume_ratio
        else:
            if logger:
                logger.log(f"[信号查询] {code} 未找到新信号")
            return None

    # ============================================================
    # ⭐ 工业级辅助方法：判断股票类型和观察名单状态
    # ============================================================
    def is_delayed_stock(self, code):
        """
        判断股票是否为延时类型
        
        参数:
            code: 股票代码 (支持 SHSE.600821 或 600821 格式)
        
        返回:
            True: 是延时股票
            False: 非延时股票
        """
        # 提取纯数字代码用于配置查找
        pure_code = code.split('.')[-1] if '.' in code else code
        
        # 获取配置（优先使用纯数字代码匹配）
        config = self.stock_personalities.get(pure_code, 
                   self.stock_personalities.get(code, 
                   self.stock_personalities.get('default', {})))
        
        stock_type = config.get('type', 'immediate')
        return stock_type == 'delayed'

    def in_watchlist(self, code):
        """
        判断股票是否在延时观察名单中
        
        参数:
            code: 股票代码 (必须与watchlist中的key一致,如 SHSE.600821)
        
        返回:
            True: 在观察名单中
            False: 不在观察名单中
        """
        return code in self.delayed_watchlist.get('watchlist', {})

    def process_signal(self, code, action, price, volume_ratio):
        """
        处理信号，判断是否加入延时观察名单
        
        注意：只处理 BUY 信号，SELL 直接返回 False
        """
        logger = get_logger()
        
        if action != "BUY":
            return False
        
        # 【修复】提取纯数字代码用于配置查找
        # 支持格式：SHSE.600821 -> 600821, SZSE.300641 -> 300641
        pure_code = code.split('.')[-1] if '.' in code else code
        
        # 获取配置（优先使用纯数字代码匹配）
        config = self.stock_personalities.get(pure_code, 
                   self.stock_personalities.get(code, 
                   self.stock_personalities.get('default', {})))
        stock_type = config.get('type', 'immediate')
        
        # 【新增】输出配置信息
        if logger:
            logger.log(f"[延时策略-检查] {code} (纯代码:{pure_code}) | 类型: {stock_type} | 量比: {volume_ratio:.2f}")
        
        if stock_type != 'delayed':
            if logger:
                logger.log(f"[延时策略-跳过] {code} 类型为 {stock_type}，非延时股票")
            return False

        # 量比过滤
        min_vr = config.get('min_volume_ratio', 18.0)
        if volume_ratio < min_vr:
            if logger:
                logger.log(f"[延时策略-跳过] {code} 量比 {volume_ratio:.2f} < 阈值 {min_vr:.2f}")
            return False
        
        # 检查是否已在观察名单中
        today = datetime.date.today()
        if code in self.delayed_watchlist.get('watchlist', {}):
            existing_item = self.delayed_watchlist['watchlist'][code]
            existing_target_date_str = existing_item.get('target_date', '')
            
            if existing_target_date_str:
                existing_target_date = datetime.datetime.strptime(existing_target_date_str, '%Y-%m-%d').date()
                
                # 【严格防护】如果已到或超过目标日，拒绝重复加入
                if today >= existing_target_date:
                    if logger:
                        logger.log(f"[延时策略-拒绝重复] {code} 已在名单中且今天是目标日，拒绝重复加入")
                    return False
                
                # 【核心原则】以第一次信号为准，禁止任何更新
                existing_signal_date = existing_item.get('signal_date', '')
                existing_vr = existing_item.get('trigger_volume_ratio', 0)
                if logger:
                    logger.log(f"[延时策略-已存在] {code} 已在名单中（信号日:{existing_signal_date}, 量比:{existing_vr:.2f}），拒绝重复写入，保持首次条件不变")
                return False
            
        # 加入名单
        signal_date = datetime.date.today()
        delay_days = max(0, int(config.get('delay_days', 1)))
        target_date = self._calculate_target_date(signal_date, delay_days)
        
        # 【新增】读取目标日最小量比配置，默认0.2
        target_day_min_vr = config.get('target_day_min_vr', 0.2)
        
        watchlist_item = {
            'name': config.get('name', code),
            'action': 'BUY',
            'signal_date': signal_date.strftime('%Y-%m-%d'),
            'target_date': target_date.strftime('%Y-%m-%d'),
            'trigger_price': price,
            'trigger_volume_ratio': volume_ratio,
            'target_day_min_vr': target_day_min_vr,  # 【新增】保存目标日最小量比
            'status': 'waiting',
            'delay_days': delay_days
        }
        
        self.delayed_watchlist['watchlist'][code] = watchlist_item
        self._save_watchlist()
        
        if logger:
            logger.log(f"[延时策略] {code} 已加入观察名单，目标日: {target_date}，目标日最小量比: {target_day_min_vr}")
        return True

    def _calculate_target_date(self, signal_date, delay_days):
        """计算目标日期（跳过周末）"""
        target = signal_date
        remaining = delay_days
        safety_counter = 0
        
        while remaining > 0 and safety_counter < 50:
            target += datetime.timedelta(days=1)
            if target.weekday() < 5:  # 跳过周末
                remaining -= 1
            safety_counter += 1
            
        return target

    def check_and_execute(self):
        """
        检查观察名单,判断是否到达目标日期并执行买入
        
        ⭐ 工业级延时策略核心逻辑(三阶段控制):
        
        ① target_date 之前 → 禁止买入(无论量比多少)
        ② target_date 当天 → 两种情况:
           - 情况A: 盘中量比 ≥ trigger_volume_ratio → 立即提前买入 → 删除watchlist
           - 情况B: 盘中量比始终 < trigger_volume_ratio → 14:39保底买入 → 删除watchlist
        ③ target_date 之后 → 延时策略过期 → 自动删除watchlist(不再买入)
        
        执行逻辑:
        - 路径 A(信号优先): 量比达到门槛 → 立即买入
        - 路径 B(保底机制): 14:39 之后 → 强制买入
        """
        logger = get_logger()
        watchlist = self.delayed_watchlist.get('watchlist', {})
        
        # 【新增】每次调用都输出日志,方便调试
        if logger:
            if not watchlist:
                logger.log(f"📋 [延时策略] 观察名单为空,跳过检查")
            else:
                logger.log(f"📋 [延时策略] 检查 {len(watchlist)} 只股票的观察名单...")
        
        if not watchlist:
            return
            
        today = datetime.date.today()
        now_time = datetime.datetime.now().strftime("%H%M")
        codes_to_remove = []
        
        # 【关键修复】使用 list() 创建副本，避免遍历时修改字典导致 RuntimeError
        for code, item in list(watchlist.items()):
            try:
                target_date_str = item.get('target_date', '')
                if not target_date_str:
                    continue
                    
                target_date = datetime.datetime.strptime(target_date_str, '%Y-%m-%d').date()
                
                # ==================== ① target_date 之前: 禁止买入 ====================
                if today < target_date:
                    if logger:
                        logger.log(f"[延时策略-未到目标日] {code} 目标日={target_date}, 今天={today}, 禁止买入")
                    continue
                
                # ==================== ② target_date 当天: 两种买入路径 ====================
                if today == target_date:
                    executed = False
                    
                    # 【路径 A】信号优先: 从Alphapilot最新信号中检查量比是否达标
                    try:
                        # ⭐ 关键修复：从信号文件中读取最新量比，而非实时查询
                        latest_vr = self._get_latest_signal_volume_ratio(code)
                        
                        if latest_vr and latest_vr > 0:
                            # 【修改】使用 target_day_min_vr 作为目标日判断阈值（默认0.2）
                            target_day_min_vr = item.get('target_day_min_vr', 0.2)
                            
                            if latest_vr >= target_day_min_vr:
                                if logger:
                                    logger.log(f"[延时策略-信号优先] {code} 最新量比 {latest_vr:.2f} >= 目标日最小量比 {target_day_min_vr:.2f},立即买入")
                                buy_success = self._execute_buy(code, item)
                                if buy_success:
                                    codes_to_remove.append(code)
                                    executed = True
                                else:
                                    if logger:
                                        logger.log(f"[延时策略-买入失败] {code} 资金不足或其他原因，保留在观察名单继续尝试")
                        else:
                            if logger:
                                logger.log(f"[延时策略-等待信号] {code} 目标日但未收到新信号，继续等待")
                    except Exception as e:
                        if logger:
                            logger.log(f"[警告] {code} 检查信号失败: {e}")
                    
                    if executed:
                        continue

                    # 【路径 B】保底机制: 14:39 之后强制买入
                    if now_time >= "1439":
                        if logger:
                            logger.log(f"[延时策略-保底买入] {code} 到达执行时间(14:39),执行保底买入")
                        buy_success = self._execute_buy(code, item)
                        if buy_success:
                            codes_to_remove.append(code)
                        else:
                            if logger:
                                logger.log(f"[延时策略-保底失败] {code} 资金不足，保留在观察名单，明日继续尝试")
                        continue
                    
                    # 还没到14:39,继续等待
                    if logger:
                        logger.log(f"[延时策略-等待中] {code} 目标日但未触发(当前{now_time}),继续等待")
                    continue
                
                # ==================== ③ target_date 之后: 延时策略过期 ====================
                if today > target_date:
                    if logger:
                        logger.log(f"[延时策略-已过期] {code} 目标日={target_date}, 今天={today}, 自动删除(不再买入)")
                    codes_to_remove.append(code)
                    continue
                # ==================== ③ target_date 之后: 延时策略过期 ====================
                if today > target_date:
                    if logger:
                        logger.log(f"[延时策略-已过期] {code} 目标日={target_date}, 今天={today}, 自动删除(不再买入)")
                    codes_to_remove.append(code)
                    continue
                    
            except Exception as e:
                if logger:
                    logger.log(f"[错误] 处理股票异常: {e}")
                    
        # 清理名单(买入后或删除过期)
        for code in codes_to_remove:
            if code in self.delayed_watchlist['watchlist']:
                del self.delayed_watchlist['watchlist'][code]
        if codes_to_remove:
            self._save_watchlist()
            if logger:
                logger.log(f"[延时策略-清理] 已移除 {len(codes_to_remove)} 只股票")

    def _execute_buy(self, code, item):
        """执行延时策略的买入操作"""
        logger = get_logger()
        try:
            # 【修复】使用真正的实时行情API获取价格
            latest_prices = self.engine.get_latest_prices([code])
            current_price = latest_prices.get(code)
            limit_up = 0  # 延时策略暂不需要涨停价
            
            if current_price is None or current_price <= 0:
                current_price = item.get('trigger_price', 0)
                
            if current_price <= 0:
                if logger:
                    logger.log(f"[错误] {code} 价格无效，放弃买入")
                return False
            
            # 资产查询
            asset = self.engine.query_asset()
            if not asset:
                return False
            
            available_cash = asset.get('cash', 0) * 0.98
            
            SINGLE_ORDER_CASH_RATIO = 0.8
            FIXED_ORDER_AMOUNT = 50000.0
            MIN_ORDER_VALUE = 15000
            
            if available_cash < MIN_ORDER_VALUE:
                return False
                
            target_cash = min(available_cash * SINGLE_ORDER_CASH_RATIO, FIXED_ORDER_AMOUNT)
            if target_cash < MIN_ORDER_VALUE:
                target_cash = available_cash
                
            vol = int((target_cash / current_price) // 100) * 100
            if vol < 100:
                if available_cash >= current_price * 100:
                    vol = 100
                else:
                    return False
                    
            # 下单定价
            order_price = round(current_price * 1.01, 2)
            
            if limit_up > 0 and order_price > limit_up:
                order_price = limit_up
                
            # 执行下单
            success = self.engine.order_stock(code, "BUY", vol, order_price, "DELAYED_V9")
            
            if logger:
                logger.log(f"[下单] {code} 买入 {vol} 股 @ {order_price:.2f} 元")
                
            return success
            
        except Exception as e:
            if logger:
                logger.log(f"[异常] {code} 买入失败: {e}")
            return False

    def execute(self):
        """执行延时策略"""
        logger = get_logger()
        if logger:
            logger.log("---- 开始执行延时策略 ----")
        self.check_and_execute()
        if logger:
            logger.log("---- 执行结束 ----")

    def process_recent_signals(self):
        """处理最近收到的信号（简化版）"""
        pass
