# 延时策略Alphapilot信号集成 - 完整实施报告

**Alphapilot智能体团队**  
作者: 梁子羿、侯沣睿、梁茹真  
邮箱: 497720537@qq.com | 电话: 13392077558  
日期: 2026-05-18  

---

## 📋 核心架构原则

### **Alphapilot是大脑，掘金是手脚** 🧠💪

- **Alphapilot（大脑）**：负责判断个股强弱，发送包含量比的信号
- **掘金（手脚）**：负责执行交易，不自己做判断

### **关键设计决策**
延时策略的买入决策**完全依赖Alphapilot智能体发来的信号中的量比**，而非实时查询SDK数据。

---

## 🔧 修复内容

### **问题描述**
原代码错误地使用价格对比来判断是否买入：
```python
# ❌ 错误逻辑
if current_price >= trigger_price:
    → 买入
```

### **正确逻辑**
应该从Alphapilot最新信号中读取量比进行对比：
```python
# ✅ 正确逻辑
latest_vr = _get_latest_signal_volume_ratio(code)
if latest_vr >= trigger_volume_ratio:
    → 买入
```

---

## 📝 修改文件清单

### **1. [`strategies/delayed_strategy.py`](d:\mpython\strategies\delayed_strategy.py)**

#### **新增方法：`_get_latest_signal_volume_ratio()`**
```python
def _get_latest_signal_volume_ratio(self, code):
    """
    从Alphapilot智能体发送的信号文件中读取指定股票的最新量比
    
    搜索策略:
    1. 优先搜索 signals/ 目录下的未处理信号文件
    2. 其次搜索 signals/processed/ 目录下今日的信号文件
    3. 按时间戳排序，返回最新的信号中的量比
    """
```

**功能特性**：
- ✅ 支持JSON数组和JSONL两种信号格式
- ✅ 自动提取纯数字代码进行匹配（兼容 `SHSE.600821` 和 `600821`）
- ✅ 多信号文件时自动选择时间戳最新的
- ✅ 无信号时返回 `None`
- ✅ 完整的日志输出便于调试

---

#### **修改方法：`check_and_execute()` - 路径A逻辑**
```python
# 【路径 A】信号优先: 从Alphapilot最新信号中检查量比是否达标
try:
    # ⭐ 关键修复：从信号文件中读取最新量比，而非实时查询
    latest_vr = self._get_latest_signal_volume_ratio(code)
    
    if latest_vr and latest_vr > 0:
        trigger_vr = item.get('trigger_volume_ratio', 0)
        
        if trigger_vr > 0 and latest_vr >= trigger_vr:
            if logger:
                logger.log(f"[延时策略-信号优先] {code} 最新量比 {latest_vr:.2f} >= 触发量比 {trigger_vr:.2f},立即买入")
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
```

**关键改进**：
1. ✅ 从Alphapilot信号文件读取量比，而非对比价格
2. ✅ 买入成功后才从名单删除，失败则保留继续尝试
3. ✅ 完善的负向日志输出

---

## 🧪 测试验证

### **测试脚本**: [`test_delayed_signal_vr.py`](d:\mpython\test_delayed_signal_vr.py)

### **测试结果**
```
✅ 测试1: 单个信号文件 - 成功读取量比: 3.50
✅ 测试2: 多个信号文件 - 正确返回最新量比: 4.20
✅ 测试3: 无信号的股票 - 正确返回 None
✅ 测试4: 完整流程模拟 - 买入成功，已从观察名单删除
```

### **关键日志输出**
```
[信号查询] SZSE.001309 最新量比: 3.80 (时间: 2026-05-18 16:23:58)
[延时策略-信号优先] SZSE.001309 最新量比 3.80 >= 触发量比 2.00,立即买入
[模拟下单] SZSE.001309 BUY 5000股 @ 10.10
```

---

## 📊 完整工作流程

### **阶段1: 信号日（T日）**
```
Alphapilot发送信号: {"code": "SZSE.001309", "volume_ratio": 0.17}
  ↓
SignalStrategy.process_signal()
  ↓
delayed_strat.process_signal() 检查
  ↓
是延时股票 + 量比 >= min_volume_ratio
  ↓
加入观察名单:
  - trigger_volume_ratio = 0.17
  - target_date = T + delay_days
```

---

### **阶段2: 目标日当天（T+N日）**

#### **路径A: 收到新信号（量比重复验证）**
```
Alphapilot再次发送: {"code": "SZSE.001309", "volume_ratio": 3.8}
  ↓
on_bar回调 → check_and_execute()
  ↓
_get_latest_signal_volume_ratio("SZSE.001309") → 3.8
  ↓
if 3.8 >= 0.17 (trigger_volume_ratio):
    → 立即买入 ✅
    → 从名单删除
```

**日志示例**：
```
[信号查询] SZSE.001309 最新量比: 3.80 (时间: 2026-05-18 14:01:15)
[延时策略-信号优先] SZSE.001309 最新量比 3.80 >= 触发量比 0.17,立即买入
[下单] SZSE.001309 买入 5000 股 @ 10.10 元
```

---

#### **路径B: 14:39保底（无新信号或量比不足）**
```
if now_time >= "1439" AND 路径A未触发:
    → 强制买入（相信最初的信号）
    → 从名单删除 ✅
```

**日志示例**：
```
[延时策略-保底买入] SZSE.001309 到达执行时间(14:39),执行保底买入
[下单] SZSE.001309 买入 5000 股 @ 9.85 元
```

---

### **阶段3: 目标日之后**
```
if today > target_date:
    → [延时策略-已过期] 自动删除，不再买入 ❌
```

**理由**：
- 过了目标日，个股可能已经涨停回落
- 严格过期符合风险控制原则
- 宁可错过，不可做错

---

## 💡 架构优势

### **1. 职责清晰**
- **Alphapilot**：智能判断，发送信号（大脑）
- **延时策略**：时间窗口控制，量比重复验证（协调者）
- **掘金SDK**：执行交易，获取行情（手脚）

### **2. 数据一致性**
- 量比数据完全来自Alphapilot信号，避免多源数据冲突
- 信号文件作为唯一真相来源（Single Source of Truth）

### **3. 可追溯性**
- 每个决策都有对应的信号文件支撑
- 日志完整记录量比来源和时间戳

### **4. 容错性强**
- 支持多种信号文件格式（JSON数组/JSONL）
- 无信号时优雅降级（等待或保底买入）
- 买入失败时保留在名单继续尝试

---

## ⚙️ 配置说明

### **信号文件格式要求**
```json
{
  "ts": "2026-05-18 14:01:15",
  "code": "SZSE.001309",
  "name": "德利明",
  "action": "BUY",
  "price": 719.97,
  "volume_ratio": 0.17,
  "source": "AlphaPilot_Email"
}
```

**必需字段**：
- `ts`: 时间戳（格式：`YYYY-MM-DD HH:MM:SS`）
- `code`: 股票代码（支持 `SHSE.600821` 或 `600821`）
- `action`: 动作（`BUY` 或 `SELL`）
- `volume_ratio`: 量比（浮点数）

---

### **观察名单数据结构**
```json
{
  "last_update": "2026-05-18 16:23:58",
  "watchlist": {
    "SZSE.001309": {
      "name": "德利明",
      "action": "BUY",
      "signal_date": "2026-05-15",
      "target_date": "2026-05-18",
      "trigger_price": 719.97,
      "trigger_volume_ratio": 0.17,
      "status": "waiting",
      "delay_days": 3
    }
  }
}
```

**关键字段**：
- `trigger_volume_ratio`: 触发量比阈值（从信号日保存）
- `target_date`: 目标买入日期
- `delay_days`: 延时天数

---

## 🎯 最佳实践建议

### **1. 信号频率**
- Alphapilot应在目标日当天持续发送该股票的信号
- 建议每5-10分钟发送一次，确保及时捕捉量比变化

### **2. 监控日志关键字**
```bash
# 搜索关键日志
grep "[延时策略" logs/*.log
grep "[信号查询" logs/*.log

# 重点关注
[延时策略-信号优先]    # 量比达标，立即买入
[延时策略-等待信号]    # 未收到新信号
[延时策略-保底买入]    # 14:39强制买入
[延时策略-买入失败]    # 资金不足警告
```

### **3. 异常处理**
如果发现某只股票反复出现"等待信号"：
1. 检查Alphapilot是否正常发送该股票信号
2. 检查信号文件格式是否正确
3. 确认股票代码格式是否一致（`SHSE.XXXXXX` vs `XXXXXX`）

---

## 📈 性能优化建议

### **当前实现**
每次调用 `_get_latest_signal_volume_ratio()` 都会遍历所有信号文件。

### **优化方向**（可选）
如果信号文件数量很大（>1000个），可以考虑：
1. **缓存机制**：缓存每只股票的最新信号，每分钟更新一次
2. **索引文件**：维护一个 `latest_signals.json` 索引文件
3. **数据库**：使用SQLite存储信号历史

但目前场景下（每天几十到几百个信号文件），当前实现完全够用。

---

## ✨ 总结

兄弟，这次修复完成了延时策略与Alphapilot智能体的**深度集成**：

✅ **架构正确**：Alphapilot是大脑，掘金是手脚  
✅ **逻辑清晰**：量比决策完全依赖Alphapilot信号  
✅ **测试通过**：4个测试场景全部验证通过  
✅ **日志完善**：每个分支都有明确的日志输出  

**核心价值**：
- 确保了延时策略的决策依据与Alphapilot的智能判断保持一致
- 避免了依赖不可靠的实时量比查询
- 形成了完整的"信号→观察→买入"闭环

现在你的系统已经具备了工业级的健壮性和可解释性！🚀
