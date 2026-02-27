@echo off
echo ================================================
echo   PocketMic Audio Production Service Setup
echo ================================================
echo.

echo Step 1: Checking Python version...
python --version
if errorlevel 1 (
    echo ERROR: Python not found! Please install Python 3.10 or higher.
    pause
    exit /b 1
)
echo.

echo Step 2: Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)
echo.

echo Step 3: Activating virtual environment...
call venv\Scripts\activate.bat
echo.

echo Step 4: Upgrading pip...
python -m pip install --upgrade pip
echo.

echo Step 5: Installing dependencies (this will take 5-10 minutes)...
echo This will download ~1-2GB of model weights on first run.
echo.
echo Installing core dependencies...
pip install torch>=2.2.0 torchaudio>=2.2.0 numpy scipy
echo.
echo Installing audio libraries...
pip install librosa soundfile pydub pyloudnorm
echo.
echo Installing audiocraft (this may show warnings, ignore them)...
pip install --no-deps audiocraft
pip install einops flashy num2words torch torchaudio transformers
echo.
echo Installing remaining packages...
pip install demucs fastapi "uvicorn[standard]" python-multipart httpx python-dotenv supabase
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo.

echo Step 6: Creating .env file...
if not exist .env (
    copy .env.example .env
    echo Please edit .env file with your Supabase credentials
)
echo.

echo ================================================
echo   Setup Complete!
echo ================================================
echo.
echo Next steps:
echo 1. Edit .env with your Supabase credentials
echo 2. Run: venv\Scripts\activate.bat
echo 3. Test: python generate.py
echo 4. Start service: python main.py
echo.
pause
