@echo off
echo [START] Ingredient Analysis Pipeline
echo ==============================

echo.
echo [CHECK] Checking Python installation...
python --version
if %errorlevel% neq 0 (
    echo [ERROR] Python not found! Please install Python first.
    pause
    exit /b 1
)

echo.
echo [CHECK] Checking required files...
if not exist "llama.py" (
    echo [ERROR] llama.py not found!
    pause
    exit /b 1
)
if not exist "fact_checker.py" (
    echo [ERROR] fact_checker.py not found!
    pause
    exit /b 1
)
if not exist "all_ingredients_merged[1].json" (
    echo [ERROR] all_ingredients_merged[1].json not found!
    pause
    exit /b 1
)
echo [OK] All required files found

echo.
echo [CHECK] Checking Ollama status...
powershell -Command "try { Invoke-RestMethod -Uri 'http://localhost:11434/api/tags' -TimeoutSec 3 | Out-Null; exit 0 } catch { exit 1 }"
if %errorlevel% neq 0 (
    echo [ERROR] Ollama not running! Please start Ollama first.
    echo [INFO] Run: ollama serve
    echo [INFO] Or in another terminal: ollama run gemma3:latest
    pause
    exit /b 1
) else (
    echo [OK] Ollama is running
)

echo.
echo [RUN] Running automated analysis pipeline...
echo ==============================
python run_analysis.py
if %errorlevel% neq 0 (
    echo [ERROR] Pipeline failed with error code: %errorlevel%
    echo [INFO] Check the output above for error details
    pause
    exit /b 1
)

echo.
echo [COMPLETE] Analysis complete! Check the generated JSON files.
dir *_all_comments.json *_fact_check_report.json 2>nul
pause
