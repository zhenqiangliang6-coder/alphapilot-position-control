# ⭐ 轻量级仓位控制模块 - 使用指南（最终版）

## 🎯 核心设计理念

**极简、透明、不改动任何现有逻辑**

仓位控制模块的唯一作用是：**设置仓位上限，超限拦截买入**

- ✅ 不改动策略逻辑
- ✅ 不调整买入数量  
- ✅ 不干预止损止盈
- ✅ 只是最后一道防线

---

## 📊 仓位信号定义

| CSS Class | 市场状态 | 仓位信号 | 仓位上限 | 说明 |
|-----------|---------|---------|---------|------|
| `position-high` | 上涨▲ | `1` | **100%** | 满仓操作 |
| `position-medium` | 横盘── | `0` | **50%** | 半仓操作 |
| `position-low` | 下跌▼ | `-1` | **30%** | 低仓操作 |

---

## 🔧 工作原理

### 流程图

```
策略触发买入信号
    ↓
调用 engine.order_stock(code, "BUY", volume, price)
    ↓
仓位控制器检查:
   获取当前持仓市值 / 总资产 = 仓位比例
   仓位比例 < 仓位上限?
    ↓
   YES → 允许下单 ✅
   NO  → 拦截买入 ❌
```

### 实际场景示例

**场景：信号从"上涨"变为"下跌"**

```python
初始状态:
  总资产: 300万
  持仓:   90万 (30%仓位)
  信号:   1 (上涨) → 仓位上限 100%

信号变化为-1 (下跌):
  仓位上限变为: 30%
  
后天操作:
  1. 持仓90万，无新买入
  2. 触发买入信号想买10万
     → 检查: 90/300=30% >= 30%上限
     → 结果: ❌ 拦截买入
  3. 触发止盈卖出20万
     → 持仓变为70万 (23.3%)
  4. 再触发买入信号想买10万
     → 检查: 70/300=23.3% < 30%上限
     → 结果: ✅ 允许买入
```

---

## 📂 信号源配置

### 默认路径

```
D:\ESC\ESC\forecast_report.html
```

这是AlphaPilot量化专家系统生成的A股指数预测报告。

### HTML解析逻辑

系统自动解析HTML中的表格，提取最后一行的`推荐仓位`列：

```html
<span class="position-medium">50%</span>
```

**CSS class映射：**
- `position-high` → 100%仓位
- `position-medium` → 50%仓位
- `position-low` → 30%仓位

---

## 💻 代码集成（已完成）

### main.py 初始化流程

```python
# 1. 创建仓位控制器（自动加载HTML信号）
position_control = PositionControl(engine=None)

# 2. 创建交易引擎（注入仓位控制器）
engine = TraderEngine(context, position_control=position_control)

# 3. 所有后续买入操作自动应用仓位控制
```

### TraderEngine.order_stock 集成

```python
def order_stock(self, symbol, side, volume, price=None, reason=""):
    # ⭐ 仓位控制：买入前检查
    if side.upper() == "BUY" and self.position_control:
        allowed, current_ratio, max_ratio = \
            self.position_control.check_buy_allowed(market_value, total_asset)
        
        if not allowed:
            print(f"[TraderEngine] ❌ 买入被拦截: {symbol} | 仓位{current_ratio*100:.1f}%已达上限{max_ratio*100:.0f}%")
            return None
    
    # ... 继续正常下单逻辑
```

---

## 📋 日志解读

### 正常日志

```
📊 [仓位控制] 信号加载成功: 1 → 0 (仓位系数: 50%)
```
- 含义：信号从"上涨"切换为"横盘"，仓位上限调整为50%

```
✅ [仓位控制] 买入允许 | 当前仓位: 23.3% < 上限: 50%
```
- 含义：当前仓位23.3%，未达50%上限，允许买入

### 拦截日志

```
❌ [仓位控制] 买入拦截 | 当前仓位: 50.0% >= 上限: 50%
```
- 含义：当前仓位已达上限，该次买入请求被拒绝

### 警告日志

```
⚠️ [仓位控制] 信号文件不存在: xxx，使用默认信号: 1 (100%仓位)
```
- 原因：HTML文件找不到
- 处理：fallback到100%仓位（不影响交易安全）

---

## 🚀 使用步骤

### 步骤1：确保信号文件存在

```bash
# 默认路径
D:\ESC\ESC\forecast_report.html
```

如果路径不同，修改main.py中的初始化：

```python
position_control = PositionControl(
    signal_file=r"D:\your_custom_path\forecast_report.html"
)
```

### 步骤2：启动策略

```bash
.\一键启动_AlphaPilot.cmd
```

### 步骤3：观察日志

查看以下关键日志：

1. **启动时**：`📊 [仓位控制] 信号加载成功: ...`
2. **运行时**：`✅ [仓位控制] 买入允许 / ❌ [仓位控制] 买入拦截`

---

## 🔍 高级配置

### 自定义刷新频率

编辑 `utils/heartbeat.py`，找到仓位控制相关代码：

```python
# 第130行左右，默认5分钟刷新
if self.position_control and (current_ts - self.last_account_print >= 300):
    self.position_control.check_and_reload_signal(reload_interval_minutes=5)
```

改为其他间隔：

```python
self.position_control.check_and_reload_signal(reload_interval_minutes=10)  # 10分钟
```

### 临时禁用仓位控制

```python
# main.py 中
engine = TraderEngine(context, position_control=None)  # 传None即可
```

---

## ✨ 关键特性

### 1. 容错性

- HTML文件不存在 → fallback到100%仓位
- HTML格式错误 → 记录日志，使用上次有效信号
- 信号值超出范围 → 自动修正到[-1, 0, 1]

### 2. 非侵入性

- 不改动任何策略文件（signal_strategy.py等）
- 不改动风控文件（stop_loss.py, dynamic_take_profit.py）
- 只修改了TraderEngine的order_stock方法

### 3. 实时性

- 每5分钟自动刷新信号
- 信号变化时自动更新仓位上限
- 日志记录完整的信息

---

## 📝 总结

**仓位控制模块的核心价值：**

1. **风险控制**：防止在下跌趋势中过度暴露在市场中
2. **智能适应**：根据专家系统预测自动调整风险敞口
3. **零侵入**：完全不影响现有策略和风控逻辑
4. **透明可追溯**：所有决策都有详细日志记录

**您只需要：**
- 确保 `D:\ESC\ESC\forecast_report.html` 正常生成
- 启动策略后观察日志
- 其他一切交由系统自动处理

---

**AlphaPilot智能体团队**  
作者: 梁子羿、侯沣睿、梁茹真  
邮箱: 497720537@qq.com | 电话: 13392077558
