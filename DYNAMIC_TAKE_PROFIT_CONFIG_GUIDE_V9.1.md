# 动态止盈配置指南

**Alphapilot智能体团队**  
作者: 梁子羿、侯沣睿、梁茹真  
邮箱: 497720537@qq.com | 电话: 13392077558

---

## 📋 概述

动态止盈模块的所有可调参数已统一提取到 [`config/settings.py`](file://d:\mpython\config\settings.py) 配置文件中，实现了与止损模块一致的**配置化管理**。

现在你只需修改配置文件，无需触碰业务代码即可调整止盈策略！

---

## 🔧 配置参数说明

所有止盈参数位于 [`config/settings.py`](file://d:\mpython\config\settings.py) 的 `[动态止盈策略 - V9.1]` 章节：

### 1. 时间控制参数

| 参数名 | 默认值 | 说明 | 调整建议 |
|--------|--------|------|---------|
| `TAKE_PROFIT_EARLIEST_TIME` | `"0951"` | 止盈最早执行时间（HHMM格式） | - `"0930"`: 开盘即执行<br>- `"1000"`: 延迟到10点<br>- `"0945"`: 推荐值 |

**作用**：避开开盘前5-10分钟的剧烈波动，防止误触发止盈。

### 2. 第一级止盈参数（快速止盈 - 所有股票）

| 参数名 | 默认值 | 说明 | 调整建议 |
|--------|--------|------|---------|
| `TAKE_PROFIT_LEVEL1_GAIN_THRESHOLD` | `0.03` | 上涨阈值（3%） | - `0.02`: 更敏感<br>- `0.05`: 更保守 |
| `TAKE_PROFIT_LEVEL1_GAIN_MAX` | `0.085` | 涨幅上限（8.5%） | - 超过此值交由第二/三级处理<br>- 通常不需调整 |
| `TAKE_PROFIT_LEVEL1_DROP_THRESHOLD` | `0.013` | 回落阈值（1.3%） | - `0.01`: 更敏感<br>- `0.02`: 更保守 |

**触发逻辑**：
```
最高涨幅 ≥ 3% 且 ≤ 8.5%
当前涨幅 ≤ 最高涨幅 - 1.3%
→ 立即卖出全部持仓
```

### 3. 第二级止盈参数（波段止盈 - 60/00开头股票）

| 参数名 | 默认值 | 说明 | 调整建议 |
|--------|--------|------|---------|
| `TAKE_PROFIT_LEVEL2_GAIN_THRESHOLD` | `0.09` | 上涨阈值（9%） | - `0.08`: 更敏感<br>- `0.10`: 更保守 |
| `TAKE_PROFIT_LEVEL2_HOLD_MINUTES` | `12` | 持有时间（分钟） | - `10`: 更快卖出<br>- `15`: 更保守 |

**触发逻辑**：
```
股票代码以 60 或 00 开头
当前涨幅 ≥ 9%
持有时间 ≥ 12 分钟
→ 卖出全部持仓
```

### 4. 第三级止盈参数（强势股止盈 - 68/30开头股票）

| 参数名 | 默认值 | 说明 | 调整建议 |
|--------|--------|------|---------|
| `TAKE_PROFIT_LEVEL3_GAIN_THRESHOLD` | `0.18` | 上涨阈值（18%） | - `0.15`: 更敏感<br>- `0.20`: 更保守 |
| `TAKE_PROFIT_LEVEL3_HOLD_MINUTES` | `12` | 持有时间（分钟） | - `10`: 更快卖出<br>- `15`: 更保守 |

**触发逻辑**：
```
股票代码以 68 或 30 开头（科创板/创业板）
当前涨幅 ≥ 18%
持有时间 ≥ 12 分钟
→ 卖出全部持仓
```

---

## 🎯 常见配置场景

### 场景1：更激进的止盈策略（快速获利了结）

```python
# config/settings.py

# 时间控制
TAKE_PROFIT_EARLIEST_TIME = "0935"  # 提前到9:35

# 第一级：更敏感
TAKE_PROFIT_LEVEL1_GAIN_THRESHOLD = 0.02    # 2% 就触发
TAKE_PROFIT_LEVEL1_DROP_THRESHOLD = 0.01    # 回落1%就卖出

# 第二级：更快
TAKE_PROFIT_LEVEL2_GAIN_THRESHOLD = 0.08    # 8% 就触发
TAKE_PROFIT_LEVEL2_HOLD_MINUTES = 10        # 持有10分钟

# 第三级：更快
TAKE_PROFIT_LEVEL3_GAIN_THRESHOLD = 0.15    # 15% 就触发
TAKE_PROFIT_LEVEL3_HOLD_MINUTES = 10        # 持有10分钟
```

### 场景2：更保守的止盈策略（让利润奔跑）

```python
# config/settings.py

# 时间控制
TAKE_PROFIT_EARLIEST_TIME = "1000"  # 延迟到10:00

# 第一级：更保守
TAKE_PROFIT_LEVEL1_GAIN_THRESHOLD = 0.05    # 5% 才触发
TAKE_PROFIT_LEVEL1_DROP_THRESHOLD = 0.02    # 回落2%才卖出

# 第二级：更保守
TAKE_PROFIT_LEVEL2_GAIN_THRESHOLD = 0.10    # 10% 才触发
TAKE_PROFIT_LEVEL2_HOLD_MINUTES = 15        # 持有15分钟

# 第三级：更保守
TAKE_PROFIT_LEVEL3_GAIN_THRESHOLD = 0.20    # 20% 才触发
TAKE_PROFIT_LEVEL3_HOLD_MINUTES = 15        # 持有15分钟
```

### 场景3：震荡市策略（快速止盈，防止利润回吐）

```python
# config/settings.py

# 时间控制
TAKE_PROFIT_EARLIEST_TIME = "0945"  # 9:45开始

# 第一级：快速止盈
TAKE_PROFIT_LEVEL1_GAIN_THRESHOLD = 0.03    # 3%
TAKE_PROFIT_LEVEL1_DROP_THRESHOLD = 0.01    # 回落1%立即卖出

# 第二级：中短期波段
TAKE_PROFIT_LEVEL2_GAIN_THRESHOLD = 0.09    # 9%
TAKE_PROFIT_LEVEL2_HOLD_MINUTES = 12        # 12分钟

# 第三级：强势股快速止盈
TAKE_PROFIT_LEVEL3_GAIN_THRESHOLD = 0.18    # 18%
TAKE_PROFIT_LEVEL3_HOLD_MINUTES = 12        # 12分钟
```

### 场景4：牛市策略（让利润奔跑）

```python
# config/settings.py

# 时间控制
TAKE_PROFIT_EARLIEST_TIME = "1000"  # 10:00开始，避开开盘波动

# 第一级：放宽快速止盈
TAKE_PROFIT_LEVEL1_GAIN_THRESHOLD = 0.05    # 5% 才触发
TAKE_PROFIT_LEVEL1_DROP_THRESHOLD = 0.015   # 回落1.5%才卖出

# 第二级：中长期波段
TAKE_PROFIT_LEVEL2_GAIN_THRESHOLD = 0.12    # 12% 才触发
TAKE_PROFIT_LEVEL2_HOLD_MINUTES = 15        # 持有15分钟

# 第三级：强势股长期持有
TAKE_PROFIT_LEVEL3_GAIN_THRESHOLD = 0.25    # 25% 才触发
TAKE_PROFIT_LEVEL3_HOLD_MINUTES = 15        # 持有15分钟
```

---

##  修改步骤

### 1. 打开配置文件

```bash
# 使用任意文本编辑器打开
notepad d:\mpython\config\settings.py
```

或使用 VSCode：
```bash
code d:\mpython\config\settings.py
```

### 2. 找到止盈参数章节

定位到 `[动态止盈策略 - V9.1]` 部分：

```python
# --- [动态止盈策略 - V9.1] ---
TAKE_PROFIT_EARLIEST_TIME = "0951"
TAKE_PROFIT_LEVEL1_GAIN_THRESHOLD = 0.03
# ... 其他参数
```

### 3. 修改参数值

根据你的策略需求，修改对应的参数值。例如：

```python
# 修改前
TAKE_PROFIT_LEVEL1_GAIN_THRESHOLD = 0.03

# 修改后（更敏感）
TAKE_PROFIT_LEVEL1_GAIN_THRESHOLD = 0.02
```

### 4. 保存并重启策略

1. 保存配置文件
2. 在掘金终端中**重启策略**
3. 观察日志输出，确认参数生效

---

##  验证配置生效

重启策略后，查看日志输出：

### 正常日志示例

```
[止盈检查] 开始执行 (当前时间:09:55:00, 最早执行:09:51)
[止盈检查] 发现 13 只持仓股票，开始检查...
[止盈分析] SZSE.301358 成本:86.50 现价:94.50 盈亏:9.24%
[止盈跳过] SZSE.301358 涨幅9.24% < 18%，未进入第三级止盈监控
[止盈总结] 本轮未触发任何止盈
```

### 检查关键点

1. **时间检查**：`最早执行:09:51` 应与配置文件一致
2. **止盈分析**：每只股票都有分析日志
3. **阈值判断**：日志中的百分比应与配置的阈值匹配

---

## ⚠️ 注意事项

### 1. 参数范围建议

| 参数 | 最小值 | 最大值 | 说明 |
|------|--------|--------|------|
| `TAKE_PROFIT_EARLIEST_TIME` | `"0930"` | `"1030"` | 时间格式必须为HHMM |
| `TAKE_PROFIT_LEVEL1_GAIN_THRESHOLD` | `0.01` | `0.10` | 1%-10% |
| `TAKE_PROFIT_LEVEL1_DROP_THRESHOLD` | `0.005` | `0.03` | 0.5%-3% |
| `TAKE_PROFIT_LEVEL2_GAIN_THRESHOLD` | `0.05` | `0.15` | 5%-15% |
| `TAKE_PROFIT_LEVEL2_HOLD_MINUTES` | `5` | `30` | 5-30分钟 |
| `TAKE_PROFIT_LEVEL3_GAIN_THRESHOLD` | `0.10` | `0.30` | 10%-30% |
| `TAKE_PROFIT_LEVEL3_HOLD_MINUTES` | `5` | `30` | 5-30分钟 |

### 2. 配置一致性

- 第一级上限 `TAKE_PROFIT_LEVEL1_GAIN_MAX` 应大于第一级阈值
- 第二级阈值应大于第一级上限
- 第三级阈值应大于第二级阈值

**推荐配置**：
```
第一级: 3% 触发, 8.5% 上限
第二级: 9% 触发
第三级: 18% 触发
```

### 3. 重启策略

**修改配置文件后必须重启策略**，否则新参数不会生效！

重启步骤：
1. 在掘金终端中停止策略
2. 重新启动策略
3. 观察日志确认参数生效

---

## 🎯 与止损模块对比

### 配置风格一致性

**止损模块**（`config/settings.py`）：
```python
# --- [风控策略 - V9.1] ---
STOP_LOSS_MONITOR_THRESHOLD = 0.005     # -0.5%
STOP_LOSS_LEVEL1_THRESHOLD = 0.012      # -1.2%
STOP_LOSS_LEVEL2_THRESHOLD = 0.025      # -2.5%
STOP_LOSS_CHECK_INTERVAL = 30           # 30秒
STOP_LOSS_START_TIME = "1045"           # 10:45
STOP_LOSS_END_TIME = "1450"             # 14:50
```

**止盈模块**（`config/settings.py`）：
```python
# --- [动态止盈策略 - V9.1] ---
TAKE_PROFIT_EARLIEST_TIME = "0951"      # 09:51
TAKE_PROFIT_LEVEL1_GAIN_THRESHOLD = 0.03    # 3%
TAKE_PROFIT_LEVEL1_GAIN_MAX = 0.085         # 8.5%
TAKE_PROFIT_LEVEL1_DROP_THRESHOLD = 0.013   # 1.3%
TAKE_PROFIT_LEVEL2_GAIN_THRESHOLD = 0.09    # 9%
TAKE_PROFIT_LEVEL2_HOLD_MINUTES = 12        # 12分钟
TAKE_PROFIT_LEVEL3_GAIN_THRESHOLD = 0.18    # 18%
TAKE_PROFIT_LEVEL3_HOLD_MINUTES = 12        # 12分钟
```

**优势**：
- ✅ 统一的命名规范（`TAKE_PROFIT_` 前缀）
- ✅ 清晰的参数分组（按止盈级别）
- ✅ 完整的注释说明（默认值 + 用途）
- ✅ 与止损模块一致的配置风格

---

## 📞 技术支持

如遇到问题，请提供：
1. 修改后的配置参数值
2. 策略重启后的日志输出
3. 当前系统时间
4. 触发止盈的股票代码和涨跌幅

**Alphapilot智能体团队**  
邮箱: 497720537@qq.com | 电话: 13392077558

---

## ✅ 总结

现在止盈模块已实现**完全配置化**：

1. ✅ 所有参数提取到 `config/settings.py`
2. ✅ 与止损模块保持一致的配置风格
3. ✅ 无需修改业务代码即可调整策略
4. ✅ 提供详细的配置指南和常见场景
5. ✅ 参数命名规范，易于理解和维护

**你可以通过修改配置文件，快速调整止盈策略，适应不同的市场环境！** 🚀
