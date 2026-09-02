# -*- coding: utf-8 -*-
"""
AlphaPilot Pro - 轻量级仓位控制模块（极简上位版）
Alphapilot智能体团队
作者: 梁子羿、侯沣睿、梁茹真
邮箱: 497720537@qq.com | 电话: 13392077558

版本: V1.2 - 仓位上限控制

功能说明:
- 从 D:\ESC\ESC\forecast_report.html 读取A股指数预测
- 解析HTML表格中的"推荐仓位"转换为仓位系数
- 信号→仓位系数映射:
  - "上涨"(position-high) → 1 (100%仓位上限)
  - "横盘"(position-medium) → 0 (50%仓位上限)
  - "下跌"(position-low) → -1 (30%仓位上限)
- 唯一作用：在买入前检查当前仓位是否超过上限
- 不改动任何策略逻辑，不调整买入数量
"""

import os
import datetime
from html.parser import HTMLParser
from utils.logger import get_logger


class TableParser(HTMLParser):
    """简易HTML表格解析器"""
    
    def __init__(self):
        super().__init__()
        self.in_table = False
        self.in_row = False
        self.in_cell = False
        self.current_cell = None
        self.cells = []
        self.rows = []
        
    def handle_starttag(self, tag, attrs):
        if tag == 'table':
            self.in_table = True
        elif tag == 'tr' and self.in_table:
            self.in_row = True
            self.cells = []
        elif tag == 'td' and self.in_row:
            self.in_cell = True
            self.current_cell = ''
        elif tag == 'span' and self.in_cell:
            for attr in attrs:
                if attr[0] == 'class' and attr[1] in ['position-high', 'position-medium', 'position-low']:
                    if hasattr(self, 'cell_classes'):
                        self.cell_classes.append(attr[1])
                    else:
                        self.cell_classes = [attr[1]]
        
    def handle_data(self, data):
        if self.in_cell and data.strip():
            self.current_cell += data.strip()
            
    def handle_endtag(self, tag):
        if tag == 'td' and self.in_cell:
            self.in_cell = False
            self.cells.append({
                'text': self.current_cell.strip(),
                'class': getattr(self, 'cell_classes', [])
            })
            if hasattr(self, 'cell_classes'):
                delattr(self, 'cell_classes')
        elif tag == 'tr' and self.in_row:
            self.in_row = False
            if self.cells:
                self.rows.append(self.cells)
        elif tag == 'table' and self.in_table:
            self.in_table = False


class PositionControl:
    """极简仓位控制器 - 仓位上限控制"""
    
    POSITION_CLASS_MAP = {
        'position-high': {'label': '100%', 'signal': 1},
        'position-medium': {'label': '50%', 'signal': 0}, # ✅ 将50%改为25%
        'position-low': {'label': '30%', 'signal': -1}
    }
    
    def __init__(self, engine=None, signal_file=None):
        """
        初始化仓位控制器
        
        参数:
            engine: 交易引擎实例（可选）
            signal_file: 信号文件路径（默认使用 D:\ESC\ESC\forecast_report.html）
        """
        self.engine = engine
        log = get_logger()
        
        # 信号文件路径
        if signal_file is None:
            self.signal_file = r"D:\ESC\ESC\forecast_report.html"
        else:
            self.signal_file = signal_file
            
        # 当前仓位信号和系数
        self.position_signal = 1
        self.position_ratio = 1.0
        
        # 启动时加载信号
        self._load_signal()
    
    def _parse_html(self, html_content):
        """
        解析HTML文件，提取综合仓位信号
        
        返回:
            int: 1(上涨), 0(横盘), -1(下跌)，解析失败返回None
        """
        parser = TableParser()
        
        try:
            parser.feed(html_content)
        except Exception as e:
            log = get_logger()
            if log:
                log.log(f"⚠️ [仓位控制] HTML解析失败: {e}")
            return None
        
        if not parser.rows or len(parser.rows) < 2:
            return None
        
        last_row = parser.rows[-1]
        
        for cell in last_row:
            if isinstance(cell, dict) and 'class' in cell:
                for css_class, info in self.POSITION_CLASS_MAP.items():
                    if css_class in cell['class']:
                        return info['signal']
        
        return None
    
    def _load_signal(self):
        """加载仓位信号"""
        log = get_logger()
        
        try:
            if not os.path.exists(self.signal_file):
                log.log(f"⚠️ [仓位控制] 信号文件不存在: {self.signal_file}，使用默认信号: 1 (100%仓位)")
                return
            
            with open(self.signal_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            signal_value = self._parse_html(html_content)
            
            if signal_value is None:
                log.log("⚠️ [仓位控制] HTML解析失败，使用默认信号: 1 (100%仓位)")
                return
            
            old_signal = self.position_signal
            self.position_signal = signal_value
            self._update_position_ratio()
            
            log.log(f"📊 [仓位控制] 信号加载成功: {old_signal} → {self.position_signal} "
                   f"(仓位系数: {self.position_ratio*100:.0f}%)")
            
        except Exception as e:
            log.log(f"⚠️ [仓位控制] 信号加载失败: {e}，使用默认信号: 1 (100%仓位)")
    
    def _update_position_ratio(self):
        """根据信号更新仓位系数"""
        if self.position_signal == 1:
            self.position_ratio = 1.0
        elif self.position_signal == 0:
            self.position_ratio =0.5 # ✅ 将50%改为25%
        elif self.position_signal == -1:
            self.position_ratio = 0.3
        else:
            self.position_ratio = 1.0
    
    def check_buy_allowed(self, current_market_value, total_asset):
        """
        检查是否允许买入（仓位上限控制）
        
        参数:
            current_market_value: 当前持仓市值
            total_asset: 总资产
            
        返回:
            tuple: (allowed: bool, current_ratio: float, max_ratio: float)
                - allowed: 是否允许买入
                - current_ratio: 当前仓位比例
                - max_ratio: 最大仓位上限
        """
        if total_asset <= 0:
            return False, 0, self.position_ratio
        
        current_ratio = current_market_value / total_asset
        max_ratio = self.position_ratio
        
        allowed = current_ratio < max_ratio
        
        log = get_logger()
        if log and allowed:
            log.log(f"✅ [仓位控制] 买入允许 | 当前仓位: {current_ratio*100:.1f}% < 上限: {max_ratio*100:.0f}%")
        elif log and not allowed:
            log.log(f"❌ [仓位控制] 买入拦截 | 当前仓位: {current_ratio*100:.1f}% >= 上限: {max_ratio*100:.0f}%")
        
        return allowed, current_ratio, max_ratio
    
    def check_and_reload_signal(self, reload_interval_minutes=30):
        """
        定期检查并重新加载信号
        
        参数:
            reload_interval_minutes: 重新加载间隔（分钟）
        """
        log = get_logger()
        
        if not hasattr(self, '_last_load_time'):
            self._last_load_time = datetime.datetime.now()
            return
        
        elapsed = (datetime.datetime.now() - self._last_load_time).total_seconds() / 60
        
        if elapsed >= reload_interval_minutes:
            log.log(f"🔄 [仓位控制] 距离上次加载已过{elapsed:.1f}分钟，重新加载信号...")
            
            old_signal = self.position_signal
            self._load_signal()
            self._last_load_time = datetime.datetime.now()
            
            if old_signal != self.position_signal:
                log.log(f"📊 [仓位控制] 信号变化: {old_signal} → {self.position_signal} "
                       f"(仓位系数: {self.position_ratio*100:.0f}%)")
