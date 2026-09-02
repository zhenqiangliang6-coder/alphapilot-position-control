# AlphaPilot智能体 - 跨平台接入快速参考卡

**核心原则**: 🚨 **字段验证优先,严禁跳过!** 🚨

---

## 🔍 5步标准化流程 (必须严格执行)

### ✅ 第1步: 字段探测脚本
```python
# 运行前必须先获取完整字段列表
positions = platform_api.get_positions()
print(type(positions[0]))  # dict or object?
print(positions[0].keys() if isinstance(positions[0], dict) else dir(positions[0]))
```

### ✅ 第2步: 创建映射表
```markdown
| 系统标准 | 平台字段 | 说明 |
|---------|---------|------|
| can_use_volume | available_now | T+1后可卖数量 |
| cost_price | vwap_open | 成本价(优先) |
```

### ✅ 第3步: 封装适配器
```python
class PlatformAdapter:
    def normalize_position(self, raw):
        return Position(
            can_use_volume=raw.get("available_now", 0),  # ✅ 已验证字段
            cost_price=self._get_cost_price(raw)
        )
```

### ✅ 第4步: 单元测试
```python
def test_t1_compliance():
    pos = adapter.normalize_position(mock_data)
    assert pos.can_use_volume == 200  # ✅ 不是1800
```

### ✅ 第5步: 生成报告
- 记录所有字段发现
- 记录特殊规则(T+1、最小交易单位等)
- 记录代码修改清单
- 多人审查签字

---

## 🚫 禁止行为 (违者必究)

❌ 未验证字段含义就写业务逻辑  
❌ 凭直觉猜测字段名(如 `available` ≠ 可卖数量)  
❌ 跳过单元测试直接集成  
❌ 不记录字段映射决策过程  

---

## ✅ 强制执行检查清单

开始编码前,必须完成:

- [ ] 运行字段探测脚本
- [ ] 创建字段映射表文档
- [ ] 实现平台适配器
- [ ] 编写单元测试并全部通过
- [ ] 生成接入报告
- [ ] 至少2人代码审查
- [ ] 沙盒环境测试通过
- [ ] 更新CHANGELOG

**未完成以上检查,严禁进入业务逻辑开发阶段!**

---

## 📊 常见陷阱速查

| 陷阱 | 表现 | 解决方案 |
|------|------|---------|
| T+1字段错误 | 尝试卖出今日买入股票 | 使用 `available_now` 而非 `available` |
| 数量非100倍数 | 下单被拒绝 | `(volume // 100) * 100` |
| 成本价为0 | 止损计算错误 | 多级Fallback: `vwap_open > vwap > cost/volume` |
| 返回类型错误 | AttributeError | 先 `type()` 检查是dict还是object |

---

## 💡 最佳实践

1. **先探测,后开发**: 花1小时探测字段,节省10小时调试
2. **文档先行**: 映射表必须在代码之前完成
3. **多人验证**: 至少2人独立验证关键字段
4. **持续更新**: 平台SDK升级后重新验证

---

**记住**: 再优秀的策略逻辑,如果字段映射错误,一切都是零!

**Alphapilot智能体团队** | 497720537@qq.com | 13392077558
