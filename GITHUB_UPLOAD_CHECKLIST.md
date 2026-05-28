# 📦 AlphaPilot Pro V9.1 - 轻量级仓位控制模块 GitHub 上传清单

## ✅ 必传核心文件

### 1. 核心功能模块

| 文件路径 | 说明 | 状态 |
|---------|------|------|
| `risk/position_control.py` | ⭐ 仓位控制核心模块（207行） | ✅ 必传 |
| `risk/__init__.py` | 风控模块导出文件 | ✅ 必传 |

### 2. 集成修改文件

| 文件路径 | 修改内容 | 状态 |
|---------|---------|------|
| `main.py` | 初始化并注入position_control | ✅ 必传 |
| `core/trader_engine.py` | order_stock加入仓位检查 | ✅ 必传 |
| `utils/heartbeat.py` | 每5分钟刷新信号 | ✅ 必传 |

### 3. 文档文件

| 文件名 | 内容 | 状态 |
|-------|------|------|
| `README.md` | GitHub版完整使用指南 | ✅ 必传 |
| `POSITION_CONTROL_GUIDE_FINAL.md` | 详细使用手册 | ✅ 必传 |
| `POSITION_CONTROL_VERIFICATION.md` | 验证报告和测试 | ✅ 必传 |
| `BUGFIX_INTEGRATION.md` | Bug修复记录 | ✅ 可选 |

### 4. 配置文件

| 文件名 | 说明 | 状态 |
|-------|------|------|
| `.gitignore` | Git忽略规则 | ✅ 必传 |

---

## 🚫 不建议上传的文件

### 日志和数据文件

```
❌ logs/*.log              # 日志文件太大
❌ data/*.json             # 用户数据
❌ signals/*.json          # 运行时信号文件
```

**理由**: 这些文件体积大、包含个人信息，且可以在本地重新生成。

### 临时和备份文件

```
❌ *.tmp
❌ *.bak
❌ *~
❌ __pycache__/            # Python缓存目录
```

### 虚拟环境和依赖

```
❌ quant_env/             # Python虚拟环境
❌ .venv/                 # 虚拟环境
```

**理由**: 用户在部署时会自行创建。

### 掘金IDE生成的UUID文件夹

```
❌ 188a052c-3c6d-11f1-8563-1ece51d839d6/
❌ 6901bc32-3d4b-11f1-962d-1ece51d839d6/
❌ c6897734-3d4a-11f1-962d-1ece51d839d6/
❌ main_data/             # 掘金IDE自动生成的目录
```

**理由**: 这些是掘金IDE自动生成的策略实例备份，不是项目核心代码。

---

## 📋 推荐Git命令

```bash
# 步骤1: 进入项目目录
cd d:\mpython

# 步骤2: 初始化Git仓库（如还未初始化）
git init

# 步骤3: 添加所有追踪的文件
git add .

# 步骤4: 查看状态（确认要提交的文件）
git status

# 步骤5: 提交
git commit -m "feat: 新增轻量级仓位控制模块 V1.2

- HTML信号解析（position-high/medium/low）
- 三级仓位控制（100%/50%/30%）
- 仓位上限检查而非调整数量
- 零侵入性设计
- 完善日志输出和异常处理"

# 步骤6: 推送到GitHub
git remote add origin https://github.com/yourusername/your-repo.git
git branch -M main
git push -u origin main
```

---

## 🔍 上传前检查清单

### 代码完整性

- [x] `risk/position_control.py` - 207行 ✅
- [x] `core/trader_engine.py` - 已修改 ✅
- [x] `utils/heartbeat.py` - 已修改 ✅
- [x] `main.py` - 已修改 ✅
- [x] `risk/__init__.py` - 已修改 ✅

### 文档完整性

- [x] `README.md` - GitHub版使用指南 ✅
- [x] `POSITION_CONTROL_GUIDE_FINAL.md` - 详细手册 ✅
- [x] `POSITION_CONTROL_VERIFICATION.md` - 验证报告 ✅
- [x] `.gitignore` - 忽略规则 ✅

### 测试验证

- [x] 语法检查通过 ✅
- [x] 导入测试通过 ✅
- [x] 功能测试通过 ✅
- [x] 集成测试通过 ✅

### 安全检查

- [ ] ❓ 检查.env文件是否被遗漏（已在.gitignore）
- [ ] ❓ 检查是否有硬编码的敏感信息
- [ ] ❓ 检查用户数据和日志是否应排除

---

## 📝 提交信息模板

```markdown
feat: 新增轻量级仓位控制模块 V1.2

## 变更内容
- HTML信号解析：从 forecast_report.html 读取CSS class标识
- 三级仓位控制：上涨(100%) / 横盘(50%) / 下跌(30%)
- 仓位上限检查：在买入前检查当前仓位是否超限
- 零侵入设计：不改动任何策略逻辑

## 技术细节
- position_control.py: 仓位控制器核心模块（207行）
- trader_engine.py: order_stock方法集成仓位检查
- heartbeat.py: 心跳线程每5分钟刷新信号

## 测试验证
- ✅ 语法检查通过
- ✅ 导入测试通过
- ✅ 仓位上限检查正常
- ✅ 日志输出完整

## 影响范围
- 修改文件: 5个
- 新增文件: 3个（文档）
- 代码行数: +30行（核心）+6行（配置）
```

---

## 🎯 最小上传方案（仅核心功能）

如果只想提交最核心的代码，至少需要：

```
✅ risk/position_control.py           # 核心模块
✅ risk/__init__.py                   # 导出
✅ core/trader_engine.py              # 集成点1
✅ utils/heartbeat.py                 # 集成点2
✅ main.py                            # 初始化流程
✅ README.md                          # 使用说明
✅ .gitignore                         # 忽略规则
```

这7个文件构成一个**最小可用版本**。

---

## 📊 推荐的完整上传结构

```
alphapilot-position-control/
├── risk/                           # ✅ 核心风控模块
│   ├── __init__.py
│   └── position_control.py
├── core/                           # ✅ 交易引擎（已修改）
│   └── trader_engine.py
├── utils/                          # ✅ 工具函数（已修改）
│   └── heartbeat.py
├── main.py                         # ✅ 主程序入口（已修改）
├── config/                         # 配置中心（保持原样）
├── strategies/                     # 策略模块（保持原样）
├── risk/                           # 其他风控模块（保持原样）
├── README.md                       # ✅ 使用说明
├── POSITION_CONTROL_GUIDE_FINAL.md # ✅ 详细手册
├── POSITION_CONTROL_VERIFICATION.md# ✅ 验证报告
├── BUGFIX_INTEGRATION.md           # 🔧 Bug修复记录（可选）
├── .gitignore                      # ✅ Git忽略规则
└── .env                            # ❌ 已在.gitignore中排除
```

---

## ⚠️ 重要提醒

### 上传前必须做的

1. **删除个人日志文件**
   ```bash
   rm -rf logs/*.log
   ```

2. **确保.gitignore生效**
   ```bash
   git check-ignore .env
   # 应该输出: .env
   ```

3. **检查提交列表**
   ```bash
   git status
   # 确认没有意外文件
   ```

### 可以选择的清理操作

```bash
# 清理__pycache__
find . -type d -name "__pycache__" -exec rm -rf {} +

# 清理临时文件
rm -f *.tmp *.bak *~
```

---

## 🚀 快速开始指南（用户端）

用户上传后需要做的：

```bash
# 1. Clone仓库
git clone https://github.com/username/repo.git
cd repo

# 2. 安装依赖
pip install gm python-dotenv watchdog

# 3. 配置环境变量
cp .env.example .env
# 编辑.env，填入GM_TOKEN和GM_ACCOUNT_ID

# 4. 确保信号源文件存在
# D:\ESC\ESC\forecast_report.html

# 5. 运行策略
python main.py
# 或
一键启动_AlphaPilot.cmd
```

---

**准备就绪时间**: 2026-05-28 18:42  
**上传版本**: V1.2  
**作者**: AlphaPilot智能体团队

