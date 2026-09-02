# -*- coding: utf-8 -*-
"""
AlphaPilot Pro - 智能量化交易策略引擎 (掘金量化版)
Alphapilot智能体团队
作者: 梁子羿、侯沣睿、梁茹真
邮箱: 497720537@qq.com | 电话: 13392077558

版本说明: V9.0 - 掘金量化平台专用版
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# ================= 基础路径配置 =================

# 1. 项目代码根目录 (自动获取)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR_CODE = CURRENT_DIR

# 【修复】项目根目录（用于访问根目录下的 signals 文件夹）
import sys
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ================= [路径架构] =================

# --- A. 信号输入区 ---
# 【修复】指向项目根目录的 signals 文件夹
SIGNAL_DIR_INPUT = os.path.join(PROJECT_ROOT, "signals")
SIGNAL_DIR_PROCESSED = os.path.join(SIGNAL_DIR_INPUT, "processed")

# --- B. 核心安全区 ---
BASE_DIR_SAFE = BASE_DIR_CODE
# 【修复】精英名单文件应该在 signals 目录下
STATE_FILE = os.path.join(SIGNAL_DIR_INPUT, "yesterday_holdings.json")
LOG_DIR = os.path.join(BASE_DIR_SAFE, "logs")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")  # 【修复】指向项目根目录的 data 文件夹

# ================= 掘金平台配置 =================

# 掘金 Token (从环境变量读取，建议在 .env 文件中设置)
GM_TOKEN = os.getenv('GM_TOKEN', '')

if not GM_TOKEN:
    print("⚠️  警告: 未设置 GM_TOKEN，请在 .env 文件中配置")
    print("   格式: GM_TOKEN=your_token_here")

# 策略 ID (从 .env 读取，建议在 .env 文件中设置)
STRATEGY_ID = os.getenv('STRATEGY_ID', '')

if not STRATEGY_ID:
    print("⚠️  警告: 未设置 STRATEGY_ID，请在 .env 文件中配置")
    print("   格式: STRATEGY_ID=your_strategy_id")

# 账户ID (掘金模拟账户或实盘账户)
ACCOUNT_ID = os.getenv('GM_ACCOUNT_ID', 'simulation')  # 默认使用模拟账户

# ================ 测试安全模式（便于本地联调） ================
# 在虚拟环境或运行命令前设置环境变量 TEST_SAFE_MODE=1 可启用
TEST_SAFE_MODE = os.getenv('TEST_SAFE_MODE', '0') in ('1', 'true', 'True')
if TEST_SAFE_MODE:
    # 为联调降低下单金额与仓位，防止误下大单
    FIXED_ORDER_AMOUNT = float(os.getenv('TEST_FIXED_ORDER_AMOUNT', '5000.0'))
    MIN_ORDER_VALUE = int(os.getenv('TEST_MIN_ORDER_VALUE', '1000'))
    SINGLE_ORDER_CASH_RATIO = float(os.getenv('TEST_SINGLE_ORDER_CASH_RATIO', '0.1'))


# ================= 策略参数配置 (V9.0 掘金版) =================

# --- [精英名单策略] ---
ELITE_PROFIT_THRESHOLD = 0.07 # 精英筛选阈值（浮盈 >8%）
AUCTION_SELL_RATIO = 0.95      # 竞价卖出报价系数（现价 95%）

# --- [无限加仓策略] ---
LEVEL_1_THRESHOLD = 30000.0     # 一级火箭触发阈值
LEVEL_2_THRESHOLD = 70000.0    # 二级火箭触发阈值
REPEAT_PROTECT_SECONDS = 540   # 重复下单保护时间（9 分钟）
MIN_ORDER_VALUE = 15000        # 最小下单金额

# --- [资金策略] ---
SINGLE_ORDER_CASH_RATIO = 0.8   # 每次买入可用现金比例（80%）
FIXED_ORDER_AMOUNT = 50000.0    # 单次买入金额上限（5 万元）

# --- [仓位管理] ---
INITIAL_CAPITAL_RATIO = 0.5    # 初始仓位比例（50% 总资金）
MAX_STOCK_COUNT = 20            # 最大持仓股票数量

# --- [风控策略 - V9.1] ---
STOP_LOSS_MONITOR_THRESHOLD = 0.005     # 止损监控触发阈值（-0.5%开始监控）
STOP_LOSS_LEVEL1_THRESHOLD = 0.012      # 一级止损阈值（-1.2%减半仓）⭐ 用户自定义
STOP_LOSS_LEVEL2_THRESHOLD = 0.025      # 二级止损阈值（-2.5%清仓）⭐ 用户自定义
STOP_LOSS_CHECK_INTERVAL = 30           # 止损检查频率（每 30 秒）
STOP_LOSS_START_TIME = "1045"           # 硬止损开始执行时间（10:45 后）
STOP_LOSS_END_TIME = "1450"             # 硬止损结束执行时间（14:50 前）
ENABLE_HARD_STOP = True                 # 硬止损开关

# --- [动态止盈策略 - V9.1] ---
TAKE_PROFIT_EARLIEST_TIME = "0935"      # 动态止盈最早执行时间（09:46），避开开盘剧烈波动
# 第一级：快速止盈（所有股票）
TAKE_PROFIT_LEVEL1_GAIN_THRESHOLD = 0.025    # 上涨 2.5%
TAKE_PROFIT_LEVEL1_GAIN_MAX = 0.089         # 涨幅上限 8.9%（超过此值不执行第一级，交由第二/三级处理）
TAKE_PROFIT_LEVEL1_DROP_THRESHOLD = 0.015   # 回落 1.5%
# 第二级：波段止盈（60/00 开头股票）
TAKE_PROFIT_LEVEL2_GAIN_THRESHOLD = 0.09    # 上涨 9%
TAKE_PROFIT_LEVEL2_HOLD_MINUTES = 5        # 持有 5 分钟
# 第三级：强势股止盈（68/30 开头股票）
TAKE_PROFIT_LEVEL3_GAIN_THRESHOLD = 0.18    # 上涨 18%
TAKE_PROFIT_LEVEL3_HOLD_MINUTES = 5        # 持有 5 分钟

# --- [基础参数] ---
HEARTBEAT_INTERVAL = 3          # 主循环心跳间隔（秒）

# --- [延时策略参数] ---
DELAYED_STRATEGY_CHECK_INTERVAL = 3

# ================= 掘金订阅配置 =================

# 订阅的股票列表 (根据实际持仓动态调整)
SUBSCRIBE_SYMBOLS = [
    'SHSE.601138',  # 工业富联 - 实际持仓
    # 可以添加更多你关注的股票
]

# K线周期 ('1m', '5m', '1d' 等)
BAR_PERIOD = '1d'  # 日线

# 回测/实盘模式配置
RUN_MODE = os.getenv('GM_RUN_MODE', 'live')  # 'backtest' 或 'live'

# 回测参数 (仅在回测模式下生效)
BACKTEST_START_DATE = '2024-01-01'
BACKTEST_END_DATE = '2024-12-31'
BACKTEST_INITIAL_CASH = 1000000  # 初始资金 100万
