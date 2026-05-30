@echo off
REM Jarvis Quick Start - Windows

echo.
echo 🤖 Jarvis - Getting Started
echo ============================
echo.

REM Create .env file if not exists
if not exist .env (
    echo 📝 Creating .env file...
    copy .env.example .env
    echo ⚠️  Please fill in your API keys in .env
)

echo.
echo 📦 Installing dependencies...
echo.

REM Backend setup
echo Backend setup...
if not exist backend mkdir backend

cd backend
python -m venv venv
call venv\Scripts\activate.bat
pip install -r ..\requirements_backend.txt
cd ..

echo.
echo ✓ Virtual environment ready!
echo.
echo Start the backend:
echo   cd backend
echo   venv\Scripts\activate.bat
echo   uvicorn backend_main:app --reload --port 8000
echo.
echo Start the frontend (new terminal):
echo   npm install
echo   npm run dev
echo.
echo ✓ Open http://localhost:5173
