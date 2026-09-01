@echo off
:: 1. 切换到目标目录 (使用 /d 参数同时切换盘符和路径)
cd /d D:\Python\Pythonevn

:: 2. 激活虚拟环境 (call 确保激活后继续执行后续指令)
call myenv\Scripts\activate

:: 3. 打印启动信息
echo =================================================
echo  ML Server (FastAPI) is starting in myenv...
echo  Directory: %CD%
echo =================================================

:: 4. 运行 Python 脚本
:: 注意：这里直接运行 python，它会使用已激活环境中的 python.exe
python ml_server.py

:: 5. (可选) 如果运行报错了，保持窗口可见以便查看错误原因
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] ml_server.py failed to start.
    pause
)