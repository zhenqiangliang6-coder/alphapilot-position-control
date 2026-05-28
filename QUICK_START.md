# ⚡ 仓位控制模块 - 快速参考卡

## 🎯 一句话说明

根据HTML文件中的A股指数预测，智能设置仓位上限（100%/50%/30%），超限拦截买入。

---

## 📦 核心文件（3个）

| 文件 | 作用 |
|------|------|
| `risk/position_control.py` | 仓位控制器核心 |
| `core/trader_engine.py` | 交易引擎（已集成） |
| `utils/heartbeat.py` | 心跳监控（已集成） |

---

## 🔑 关键代码（2分钟看懂）

### 初始化（main.py）

```python
# 先创建仓位控制器
position_control = PositionControl(
    signal_file=r"D:\ESC\ESC\forecast_report.html"
)

# 再创建交易引擎（注入仓位控制器）
engine = TraderEngine(context, position_control=position_control)
```

### 使用示例

```python
from risk.position_control import PositionControl

pc = PositionControl()

# 检查是否允许买入
allowed, current_ratio, max_ratio = pc.check_buy_allowed(
    current_market_value=900000,  # 当前持仓市值
    total_asset=3000000           # 总资产
)

if allowed:
    print("✅ 允许买入")
else:
    print("❌ 买入被拦截")
```

---

## 📊 三种信号

| CSS Class | 信号值 | 仓位上限 | 场景 |
|-----------|--------|---------|------|
| `position-high` | 1 | 100% | 上涨趋势 |
| `position-medium` | 0 | 50% | 横盘震荡 |
| `position-low` | -1 | 30% | 下跌趋势 |

---

## 🔍 快速调试

### 问题1: 导入失败

```bash
# 检查路径
cd d:\mpython
python -c "from risk.position_control import PositionControl; print('✅')"
```

### 问题2: HTML解析失败

```bash
# 测试解析
python demo_position_control.py
```

### 问题3: 仓位检查不生效

```bash
# 检查日志
grep "仓位控制" logs/*.log
# 应该看到:
# ✅ [仓位控制] 买入允许
# ❌ [仓位控制] 买入拦截
```

---

## 🚀 一键部署

```bash
# 克隆
git clone https://github.com/username/repo.git

# 安装依赖
pip install gm python-dotenv watchdog

# 启动
一键启动_AlphaPilot.cmd
```

---

## 📖 详细文档

- [完整使用指南](POSITION_CONTROL_GUIDE_FINAL.md)
- [验证报告](POSITION_CONTROL_VERIFICATION.md)
- [Bug修复记录](BUGFIX_INTEGRATION.md)
- [上传清单](GITHUB_UPLOAD_CHECKLIST.md)

---

**版本**: V1.2 | **更新**: 2026-05-28

