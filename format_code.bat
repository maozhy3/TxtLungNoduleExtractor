@echo off
chcp 65001 >nul
echo ========================================
echo 代码格式化和检查
echo ========================================
echo.

REM 检查是否安装了工具
python -c "import black" 2>nul
if errorlevel 1 (
    echo ❌ 未安装 black，正在安装...
    pip install black ruff
    if errorlevel 1 (
        echo ❌ 安装失败
        pause
        exit /b 1
    )
)

echo [1/3] 使用 Black 格式化代码...
echo.
black *.py tests/ --line-length 100
echo.

echo [2/3] 使用 Ruff 检查代码...
echo.
ruff check . --fix
echo.

echo [3/3] 再次运行 Ruff 检查（不自动修复）...
echo.
ruff check .

echo.
echo ========================================
echo ✓ 完成！
echo ========================================
echo.
pause
