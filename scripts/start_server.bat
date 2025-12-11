@echo off
REM Claude Voice Hooks - Local Server Startup Script
REM Phase 3: Translation + TTS Integration

echo ========================================
echo  Claude Voice Hooks Server
echo  Phase 3: Translation + TTS
echo ========================================
echo.

REM Change to project root directory
cd /d "%~dp0.."

REM Check if in correct directory
if not exist "server\app.py" (
    echo [ERROR] server\app.py not found
    echo Current directory: %CD%
    exit /b 1
)

REM Check Python is available
.venv\Scripts\python.exe --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python virtual environment not found
    echo Please run: uv venv .venv
    exit /b 1
)

REM ========================================
REM GPU Memory Optimization Settings
REM ========================================
REM Reduce VRAM fragmentation and peak usage
REM - garbage_collection_threshold: Lower threshold for more aggressive memory reclamation
REM - max_split_size_mb: Limit memory block size to reduce fragmentation
set PYTORCH_CUDA_ALLOC_CONF=garbage_collection_threshold:0.8,max_split_size_mb:64

REM Enable low-VRAM mode for GPT-SoVITS (< 1GB target)
set low_vram=True
set is_half=True

echo [INFO] GPU Settings:
echo   - PYTORCH_CUDA_ALLOC_CONF=%PYTORCH_CUDA_ALLOC_CONF%
echo   - low_vram=%low_vram%
echo   - is_half=%is_half%
echo.

echo [INFO] Starting server...
echo [INFO] Server will be available at http://127.0.0.1:8765
echo.
echo Endpoints:
echo   - GET  /health             : Health check
echo   - POST /hook               : Receive hook events
echo   - POST /translate_and_speak: Translate text and synthesize speech
echo   - GET  /                   : API info
echo.
echo Press Ctrl+C to stop the server
echo.
echo ========================================
echo.

REM Start server with uvicorn using uv environment
.venv\Scripts\python.exe -m uvicorn server.app:app --host 127.0.0.1 --port 8765 --log-level info

echo.
echo ========================================
echo Server stopped
echo ========================================
