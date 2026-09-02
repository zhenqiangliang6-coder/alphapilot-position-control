# AlphaPilot Pro V9.1 - 一键启动脚本
# Alphapilot智能体团队
# 作者: 梁子羿、侯沣睿、梁茹真
# 邮箱: 497720537@qq.com | 电话: 13392077558

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "AlphaPilot Pro V9.1 启动脚本" -ForegroundColor Cyan
Write-Host "工业级事件驱动架构" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查 Python 环境
$pythonPath = ".\quant_env\Scripts\python.exe"
if (-not (Test-Path $pythonPath)) {
    Write-Host "[错误] 未找到 Python 环境: $pythonPath" -ForegroundColor Red
    Write-Host "请先创建虚拟环境或修改脚本中的路径" -ForegroundColor Yellow
    exit 1
}

Write-Host "[1/4] 检查依赖..." -ForegroundColor Green

# 检查 watchdog
try {
    & $pythonPath -c "import watchdog; print('✓ watchdog 已安装')"
} catch {
    Write-Host "[警告] watchdog 未安装，正在安装..." -ForegroundColor Yellow
    & .\quant_env\Scripts\pip.exe install watchdog
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[错误] watchdog 安装失败" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "[2/4] 检查配置文件..." -ForegroundColor Green

# 检查关键目录
$requiredDirs = @("logs", "signals", "signals\processed", "data")
foreach ($dir in $requiredDirs) {
    if (-not (Test-Path $dir)) {
        Write-Host "[提示] 创建目录: $dir" -ForegroundColor Yellow
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

Write-Host ""
Write-Host "[3/4] 检查信号文件..." -ForegroundColor Green

$signalFiles = Get-ChildItem -Path "signals" -Filter "*.txt" -ErrorAction SilentlyContinue
if ($signalFiles) {
    Write-Host "[提示] 发现 $($signalFiles.Count) 个待处理信号文件" -ForegroundColor Yellow
} else {
    Write-Host "[提示] 无待处理信号文件" -ForegroundColor Gray
}

Write-Host ""
Write-Host "[4/4] 启动策略..." -ForegroundColor Green
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "运行模式: 实盘/模拟" -ForegroundColor White
Write-Host "日志目录: logs/" -ForegroundColor White
Write-Host "按 Ctrl+C 停止策略" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 启动策略
& $pythonPath main.py --mode live

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[错误] 策略启动失败，退出码: $LASTEXITCODE" -ForegroundColor Red
    exit 1
}
