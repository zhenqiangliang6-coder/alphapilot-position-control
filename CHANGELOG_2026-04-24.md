# 修改日志 - 2026年4月24日

**Alphapilot智能体团队**  
作者: 梁子羿、侯沣睿、梁茹真  
邮箱: 497720537@qq.com | 电话: 13392077558

---

## 📋 今日修改概览

### ⚠️ 重要工程原则确立

**核心教训**: 无论接入任何量化交易平台(QMT、掘金、聚宽、米筐等),**必须从接口完整字段列表验证开始**,这是策略正确执行的先决条件,严禁跳过此步骤直接开发业务逻辑。

**历史教训**:
1. **掘金SDK持仓字段错误**: 假设 `available` 是可卖数量 → 实际应使用 `available_now`
2. **A股交易规则遗漏**: 未对卖出数量进行100股取整,导致下单失败
3. **后果**: 即使策略逻辑再优秀,字段映射错误也会导致完全失效

**新规范**: 已建立《AlphaPilot智能体跨平台接入标准化流程规范》,包含5步强制流程和检查清单。

---

### 核心修复1: 掘金SDK持仓字段映射错误

**问题描述**:  
项目中所有卖出操作使用了错误的可平数量字段,导致可能尝试卖出今日买入的股票(违反A股T+1规则)。

**根本原因**:  
- 掘金SDK v3.0.183返回的原始持仓数据中,`available` 字段包含**总可平数量**(历史持仓 + 今日买入)
- 正确的T+1合规字段应该是 `available_now`(仅历史持仓,已扣除今日买入部分)
- Position类初始化时错误地使用了 `raw.get("available")`,应改为 `raw.get("available_now")`

---

### 核心修复2: A股交易规则 - 卖出数量必须为100的整数倍

**问题描述**:  
止损和止盈模块在计算卖出数量时,未考虑A股交易规则要求股票数量必须是100股的整数倍(1手=100股),可能导致下单失败。

**影响场景**:
- **一级止损减半**: `current_volume // 2` 可能产生非100倍数的结果(如250股)
- **集合竞价卖出**: 直接使用 `pos.can_use_volume`,可能不是100的倍数
- **即时信号卖出**: 同样直接使用可卖数量

**示例错误**:
```
# ❌ 错误: 250股无法成交
sell_volume = 500 // 2  # 结果: 250

# ✅ 正确: 向下取整到200股
sell_volume = (500 // 2 // 100) * 100  # 结果: 200
```

---

## 🔧 具体修改内容

### 1. 核心字段映射修复

**文件**: `core/trader_engine.py`  
**位置**: L50 (Position类初始化)

**修改前**:
```python
self.can_use_volume = raw.get("available", 0) if raw else 0
```

**修改后**:
```
# ⭐ 新增字段：可卖数量（止损模块需要）
# gm 3.0.183 字段说明:
# - available: 总可平数量(历史+今日买入)
# - available_now: 当前可卖数量(仅历史持仓,已扣除T+1限制) ✅ 正确字段
# - available_today: 今日买入数量(T+1不可卖)
self.can_use_volume = raw.get("available_now", 0) if raw else 0
```

**影响范围**:  
此修复自动应用到所有使用 `pos.can_use_volume` 的模块:
- ✅ `risk/stop_loss.py` - 动态止损(3处)
- ✅ `risk/dynamic_take_profit.py` - 动态止盈(3处)
- ✅ `strategies/auction_strategy.py` - 集合竞价策略(3处)
- ✅ `strategies/signal_strategy.py` - 即时信号策略(4处)

---

### 2. A股交易规则修复 - 100股取整

#### 2.1 新增辅助函数

**文件**: `utils/helpers.py`  
**新增函数**: `round_lot(volume)`

```
def round_lot(volume):
    """
    将股票数量向下取整到100的整数倍（A股交易规则：1手=100股）
    
    参数:
        volume: 原始股票数量
    
    返回:
        int: 取整后的数量（100的倍数）
    
    示例:
        >>> round_lot(250)
        200
        >>> round_lot(1800)
        1800
        >>> round_lot(99)
        0
    """
    return (volume // 100) * 100
```

#### 2.2 动态止损模块修复

**文件**: `risk/stop_loss.py`

**修复点1 - 一级止损减半** (L172):
```
# 修改前
sell_volume = current_volume // 2

# 修改后
sell_volume = current_volume // 2
# A股规则：卖出数量必须是100的整数倍
sell_volume = (sell_volume // 100) * 100
```

**修复点2 - _execute_stop_loss方法** (L257-L263):
```
# 修改前
actual_volume = min(volume, can_sell)

# 修改后
actual_volume = min(volume, can_sell)
# A股规则：卖出数量必须是100的整数倍
actual_volume = (actual_volume // 100) * 100

if actual_volume <= 0:
    log.log("[止损跳过] {} 数量不足100股，无法卖出".format(code))
    return False
```

#### 2.3 动态止盈模块修复

**文件**: `risk/dynamic_take_profit.py`  
**位置**: `_execute_sell` 方法 (L350-L391)

```
# 修改前
sell_price = round(current_price * 0.99, 2)
log.log("[止盈执行] {} 卖出 {} 股 @ {} ({})".format(code, volume, sell_price, reason))
success = self.engine.order_stock(code, "SELL", volume, sell_price, reason)

# 修改后
# A股规则：卖出数量必须是100的整数倍
actual_volume = (volume // 100) * 100

if actual_volume <= 0:
    log.log("[止盈跳过] {} 数量不足100股，无法卖出".format(code))
    return False

sell_price = round(current_price * 0.99, 2)
log.log("[止盈执行] {} 卖出 {} 股 @ {} ({})".format(code, actual_volume, sell_price, reason))
success = self.engine.order_stock(code, "SELL", actual_volume, sell_price, reason)
```

#### 2.4 集合竞价策略修复

**文件**: `strategies/auction_strategy.py`  
**位置**: L60-L64

```
# 修改前
if pos.can_use_volume <= 0:
    log.log("[竞价] {} 今日买入不可卖（总持仓:{} 可卖:0），跳过".format(code, pos.volume))
    skipped_codes.append(code)
    continue

# 修改后
sell_volume = (pos.can_use_volume // 100) * 100  # A股规则：100的整数倍

if sell_volume <= 0:
    log.log("[竞价] {} 今日买入不可卖或数量不足100股（总持仓:{} 可卖:{}），跳过".format(code, pos.volume, pos.can_use_volume))
    skipped_codes.append(code)
    continue
```

**后续下单逻辑同步修改** (L92):
```
# 修改前
if self.engine.order_stock(code, "SELL", pos.can_use_volume, sell_price, "AUCTION_ELITE"):

# 修改后
if self.engine.order_stock(code, "SELL", sell_volume, sell_price, "AUCTION_ELITE"):
```

#### 2.5 即时信号策略修复

**文件**: `strategies/signal_strategy.py`

**修复点1 - execute_sell_signal方法** (L196-L206):
```
# 修改前
if pos.can_use_volume <= 0:
    log.log(f"[卖出失败] {code} 无可用持仓，跳过")
    return False

order_price = round(price * 0.99, 2)
result = self.engine.order_stock(code, "SELL", pos.can_use_volume, order_price, "SIGNAL_V9")

# 修改后
sell_volume = (pos.can_use_volume // 100) * 100  # A股规则：100的整数倍

if sell_volume <= 0:
    log.log(f"[卖出失败] {code} 无可用持仓或数量不足100股，跳过")
    return False

order_price = round(price * 0.99, 2)
result = self.engine.order_stock(code, "SELL", sell_volume, order_price, "SIGNAL_V9")
```

**修复点2 - _check_position_and_calculate_volume方法** (L325-L336):
```
# 修改前
if not pos or pos.can_use_volume <= 0:
    return False, 0, "无可卖持仓"
return True, pos.can_use_volume, "卖出全部可用"

# 修改后
if not pos or pos.can_use_volume <= 0:
    return False, 0, "无可卖持仓"
# A股规则：卖出数量必须是100的整数倍
sell_volume = (pos.can_use_volume // 100) * 100
if sell_volume <= 0:
    return False, 0, "可卖数量不足100股"
return True, sell_volume, "卖出全部可用(已取整)"
```

---

### 3. 测试工具开发

**新增文件**: `test_position_fields.py`

**功能**:  
- 验证掘金SDK返回的持仓数据结构
- 显示所有可用字段及其含义
- 确认T+1规则相关字段的正确性

**测试结果示例**:
```
【持仓数量 - 核心字段】
  📦 总持仓 (volume): 1800 股
  ✅ 可平数量 (available): 1800 股      # ❌ 包含今日买入
  ✅ 可平数量 (available_now): 200 股   # ✅ 仅历史持仓
  📊 今日买入 (available_today): 1600 股

【T+1合规验证】
  ✅ 全部可卖：200 股 (符合T+1规则)
```

---

## 📊 掘金SDK持仓字段完整映射表

根据实际测试,掘金SDK v3.0.183返回的持仓对象包含以下关键字段:

| SDK字段 | 含义 | 示例值 | 用途 |
|---------|------|--------|------|
| `symbol` | 股票代码 | "SHSE.603538" | 标识股票 |
| `volume` | 总持仓数量 | 1800 | 显示用 |
| `available` | 总可平数量 | 1800 | ❌ **不可用于卖出**(含今日买入) |
| `available_now` | **当前可卖数量** | 200 | ✅ **止损/止盈必须用此字段** |
| `available_today` | 今日买入数量 | 1600 | 调试用,T+1不可卖 |
| `cost` | 持仓成本总额 | 103123.20 | 计算成本价 |
| `vwap` | 加权平均价 | 57.29 | 成本价备选 |
| `vwap_open` | 开仓加权平均价 | 57.29 | ✅ **优先使用的成本价** |
| `last_price` | 最新价格 | 58.63 | 实时价格 |
| `market_value` | 持仓市值 | 103680.00 | 资产计算 |
| `fpnl` | 浮动盈亏 | 556.80 | 盈亏监控 |

例子：数据类型】
  类型: <class 'gm.utils.DictLikeObject'>
  是否为字典: True

【基本信息】
  股票代码 (symbol): SHSE.603538

【持仓数量 - 核心字段】
  📦 总持仓 (volume): 1800 股
  ✅ 可平数量 (available): 1800 股
  ❌ 可平数量 (can_use_volume): 字段不存在

【T+1合规验证】
  ✅ 全部可卖：1800 股

【价格与盈亏】
  成本价 (cost): 103123.20 元
  VWAP (vwap): 57.29 元
  VWAP_Open (vwap_open): 57.29 元
  最新价 (last_price): 58.63 元
  持仓市值 (market_value): 103680.00 元
  浮动盈亏 (fpnl): 556.80 元

【完整字段列表】
  可用字段 (33个):
    account_id: ae22ac8e-3bb9-11f1-a262-00163e022aa6
    account_name: 
    amount: 103123.2000
    available: 1800
    available_now: 200
    available_today: 1600
    change_event_id: 
    change_reason: 0
    channel_id: 
    cost: 103123.2000
    covered_flag: 0
    created_at: 2026-04-20 14:39:03.025524+08:00
    credit_position_sellable_volume: 0
    fpnl: 556.7973
    fpnl_diluted: 556.7973
    fpnl_open: 556.7973
    has_dividend: 0
    last_inout: 0
    last_price: 58.6300
    last_volume: 800
    market_value: 103679.9973
    order_frozen: 0
    order_frozen_today: 0
    price: 57.6000
    properties: {}
    side: 1
    symbol: SHSE.603538
    updated_at: 2026-04-24 13:41:31.404124+08:00
    volume: 1800
    volume_today: 1600
    vwap: 57.2907
    vwap_diluted: 57.2907
    vwap_open: 57.2907

**成本价优先级**: `vwap_open` > `vwap` > `(cost / volume)`

---

## ✅ 代码审计结果

对所有涉及卖出操作的模块进行了全面审查:

### 1. risk/stop_loss.py - 动态止损
- ✅ L172: 一级止损减半后进行100股取整
- ✅ L179: 检查实际可卖数量
- ✅ L207: 二级止损清仓使用 `p.can_use_volume`
- ✅ L249: _execute_stop_loss中进行100股取整并验证
- ✅ 负向日志完善: 当 `can_sell == 0` 或 `<100` 时输出跳过原因

### 2. risk/dynamic_take_profit.py - 动态止盈
- ✅ L206: 第一级快速止盈使用 `pos.can_use_volume`
- ✅ L270: 第二级波段止盈使用 `pos.can_use_volume`
- ✅ L334: 第三级强势止盈使用 `pos.can_use_volume`
- ✅ L350: _execute_sell中进行100股取整并验证
- ✅ 每个级别都有完善的跳过日志

### 3. strategies/auction_strategy.py - 集合竞价策略
- ✅ L60: 对可卖数量进行100股取整
- ✅ L62: 检查取整后数量是否>0
- ✅ L90: 日志输出包含总持仓和可卖对比
- ✅ L92: 下单使用取整后的 `sell_volume`

### 4. strategies/signal_strategy.py - 即时信号策略
- ✅ L196: 对可卖数量进行100股取整
- ✅ L198: 检查取整后数量是否>0
- ✅ L204: 下单使用取整后的 `sell_volume`
- ✅ L334: _check_position_and_calculate_volume中进行100股取整

---

## 🎯 关键改进点

### 1. T+1规则完全合规
- ✅ 所有卖出操作都使用 `available_now` 字段
- ✅ 今日买入的股票不会被尝试卖出
- ✅ 符合A股T+1交易制度

### 2. A股交易规则合规
- ✅ 所有卖出数量都向下取整到100的整数倍
- ✅ 数量不足100股时明确跳过并记录日志
- ✅ 避免下单失败导致的策略中断

### 3. 负向日志完善
所有模块在无法卖出时都输出明确原因:
```
[止损跳过] SHSE.XXXXXX 今日买入不可卖（总持仓:XXX 可卖:0），无法执行XX止损
[止损跳过] SHSE.XXXXXX 数量不足100股，无法卖出
[止盈跳过] SHSE.XXXXXX 今日买入不可卖（总持仓:XXX 可卖:0），无法执行XX止盈
[止盈跳过] SHSE.XXXXXX 数量不足100股，无法卖出
[竞价] SHSE.XXXXXX 今日买入不可卖或数量不足100股（总持仓:XXX 可卖:XXX），跳过
```

### 4. 无硬编码错误
- ✅ 没有直接使用原始字典字段进行卖出
- ✅ 所有逻辑通过Position对象封装
- ✅ 统一使用 `pos.can_use_volume` 属性并进行100股取整

---

## 🧪 验证方法

运行测试工具验证字段映射:
```
& d:/mpython/quant_env/Scripts/python.exe d:/mpython/test_position_fields.py
```

预期输出应显示:
- `available_now` 已扣除今日买入部分
- T+1验证通过
- 完整的33个字段列表

---

## 📝 结论

**✅ 所有代码已正确使用掘金SDK字段映射并符合A股交易规则**

项目完全符合:
- ✅ 掘金SDK v3.0.183的字段规范
- ✅ A股T+1交易规则
- ✅ A股100股整数倍交易规则
- ✅ 完善的异常处理和日志记录

**无需进一步修改**,系统可以安全运行!

---

## 🔗 相关文档

- [掘金量化SDK开发与交易引擎封装规范](./GM_CONNECTION_WARNING_EXPLANATION.md)
- [持仓字段全面审计报告](./CHANGELOG_2026-04-24.md) - 本文档
- [测试工具使用说明](./test_position_fields.py)

---

**修改人**: Alphapilot智能体团队  
**审核状态**: ✅ 已完成全面审计  
**部署状态**: ✅ 可直接运行
