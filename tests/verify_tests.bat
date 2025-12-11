@echo off
REM Windows 测试验证脚本
REM 用于快速验证测试框架是否正常工作

echo ========================================
echo  Phase 1 测试框架验证
echo ========================================
echo.

echo [1/3] 检查 Python 版本...
python --version
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python 未安装或不在 PATH 中
    exit /b 1
)
echo.

echo [2/3] 检查测试依赖...
python -c "import pytest; import pytest_asyncio; import httpx" 2>NUL
if %ERRORLEVEL% NEQ 0 (
    echo [WARN] 测试依赖未安装，正在安装...
    pip install -r tests\requirements.txt
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] 依赖安装失败
        exit /b 1
    )
)
echo [OK] 测试依赖已安装
echo.

echo [3/3] 运行 Smoke Tests...
echo ----------------------------------------
pytest tests\test_smoke.py -v --tb=short
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Smoke tests 失败！
    echo 请检查测试输出了解详情。
    exit /b 1
)

echo.
echo ========================================
echo  ✅ 测试框架验证成功！
echo ========================================
echo.
echo 下一步：
echo   1. 创建 server 目录: mkdir server
echo   2. 开始实现第一个模块: server\config.py
echo   3. 运行测试: pytest tests\test_config.py -v
echo.
