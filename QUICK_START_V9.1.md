# AlphaPilot Pro V9.1 - 快速上手指南

**Alphapilot智能体团队**  
作者: 梁子羿、侯沣睿、梁茹真  
邮箱: 497720537@qq.com | 电话: 13392077558

---

## 🚀 5 分钟快速启动

### 步骤 1：安装依赖

```bash
cd d:\mpython
.\quant_env\Scripts\pip.exe install watchdog
```

### 步骤 2：一键启动

```powershell
.\start_v9_1.ps1
```

或者手动启动：

```bash
python main.py --mode live
```

### 步骤 3：观察日志

查看 `logs/alphapilot.log`，确认以下输出：

```
🚀 [日志系统] 异步日志已启动（工业级）
👁️  [watchdog] 开始监听信号目录: d:\mpython\signals
💓 [心跳] 独立心跳线程已启动（工业级瘦身版）
📡 [信号总线] 分发线程已启动
```

---

## 🧪 测试信号处理

### 创建测试信号文件

在 PowerShell 中执行：

```powershell
echo '{"code": "600821", "action": "BUY", "price": 10.5, "volume_ratio": 20.0}' > signals\test_signal.txt
```

### 预期日志输出

```
📩 [watchdog] 检测到新信号: test_signal.txt
[格式转换] 600821 -> SHSE.600821
[延时策略-检查] SHSE.600821 (纯代码:600821) | 类型: delayed | 量比: 20.00
[延时策略] SHSE.600821 已加入观察名单，目标日: 2024-XX-XX
[归档] test_signal.txt -> processed
```

---

## 📊 核心改进一览

| 特性 | V9.0 | V9.1 |
|------|------|------|
| **信号检测** | 每分钟全量扫描 | watchdog 事件触发 |
| **日志写入** | 同步阻塞 | 异步队列 |
| **心跳线程** | 10+ 项任务 | 仅心跳 + 账户信息 |
| **性能衰退** | 是（越来越慢） | 否（恒定性能） |
| **I/O 争抢** | 严重 | 无 |

---

## 🔍 常见问题

### Q1: watchdog 未检测到新文件？

**检查清单：**
1. 确认文件扩展名为 `.txt` 或 `.json`
2. 确认文件不在 `processed/` 子目录
3. 检查日志是否有 `[警告]` 信息

**调试方法：**
```python
# 在 signal_watcher.py 的 on_created 中添加
print(f"检测到文件: {event.src_path}")
```

### Q2: 日志输出延迟？

异步日志默认使用队列，正常情况下应立即输出。如果仍有延迟：

1. 检查队列是否已满（默认容量 10000）
2. 检查工作线程是否正常运行
3. 临时切换为同步日志测试：
   ```python
   # 在 logger.py 中注释掉异步逻辑
   # self.async_queue.put(formatted_msg)
   print(formatted_msg)  # 改为同步输出
   ```

### Q3: 心跳间隔不稳定？

V9.1 的心跳线程仅负责心跳和账户信息，理论上应非常稳定。如果不稳定：

1. 检查系统负载（CPU/内存占用）
2. 检查是否有其他线程占用 GIL
3. 增加心跳线程优先级：
   ```python
   import threading
   self.thread = threading.Thread(..., daemon=True)
   # Python 3.13+ 支持设置线程优先级
   ```

### Q4: 如何回退到 V9.0？

如果需要临时回退：

1. 备份当前代码：
   ```bash
   git add .
   git commit -m "Backup V9.1"
   ```

2. 恢复旧版本：
   ```bash
   git checkout <V9.0-commit-hash>
   ```

---

## 📁 目录结构

```
d:\mpython\
├── main.py                    # 主程序入口（V9.1 重构版）
├── start_v9_1.ps1            # 一键启动脚本
├── requirements.txt           # Python 依赖
├── ARCHITECTURE_V9.1.md      # 详细架构说明
├── QUICK_START_V9.1.md       # 本文件
│
├── utils/
│   ├── logger.py             # 异步日志系统 ✨新增
│   ├── heartbeat.py          # 瘦身心跳监控器 ✨新增
│   └── signal_watcher.py     # watchdog 监听器 ✨新增
│
├── core/
│   ├── trader_engine.py      # 交易引擎
│   ├── state_manager.py      # 状态管理器
│   └── signal_bus.py         # 信号总线 ✨新增
│
├── strategies/
│   ├── signal_strategy.py    # 信号策略（双模式支持）
│   ├── delayed_strategy.py   # 延时策略
│   ├── rocket_boost.py       # 火箭加仓
│   └── auction_strategy.py   # 集合竞价
│
├── risk/
│   ├── stop_loss.py          # 止损监控
│   └── dynamic_take_profit.py # 动态止盈
│
├── logs/                     # 日志目录
│   └── alphapilot.log        # 主日志文件（自动轮转）
│
└── signals/                  # 信号文件目录
    ├── *.txt                 # 待处理信号
    └── processed/            # 已处理信号（归档）
```

---

## 🎯 下一步优化建议

### 短期（1-2 周）
1. **信号去重**：在 `SignalBus` 中添加哈希去重
2. **监控面板**：开发 Web UI 实时显示策略状态
3. **告警通知**：集成钉钉/企业微信告警

### 中期（1-2 月）
1. **持久化队列**：使用 Redis 实现高可用信号总线
2. **分布式部署**：支持多机协同处理信号
3. **性能分析**：集成 cProfile 定期生成性能报告

### 长期（3-6 月）
1. **微服务化**：将各模块拆分为独立服务
2. **容器化部署**：使用 Docker + Kubernetes
3. **机器学习集成**：引入 AI 模型优化策略参数

---

## 📞 技术支持

如有问题，请联系 Alphapilot智能体团队：
- 邮箱: 497720537@qq.com
- 电话: 13392077558

---

**祝您交易顺利！🚀**
