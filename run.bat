@echo off
echo 🚀 Starting WhatsApp Automation Bot for Windows...

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Error: python is not installed. Please install it from python.org
    pause
    exit /b
)

:: Set up virtual environment if it doesn't exist
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

:: Activate virtual environment
echo 🔌 Activating virtual environment...
call venv\Scripts\activate

:: Upgrade pip and setuptools to ensure we can find pre-built wheels
echo 🔧 Upgrading pip and build tools...
python -m pip install --upgrade pip setuptools wheel

:: Install dependencies
echo 📥 Checking dependencies...
pip install -r requirements.txt

:: Run the Streamlit app
echo 🌐 Launching Streamlit dashboard on port 8501...
streamlit run app.py --server.port 8501

pause
