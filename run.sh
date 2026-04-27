#!/bin/bash

# --- WhatsApp Bot Run Script ---

# Navigate to the project directory
cd "$(dirname "$0")"

echo "🚀 Starting WhatsApp Automation Bot..."

# Check if Python is installed
if ! command -v python3 &> /dev/null
then
    echo "❌ Error: python3 is not installed. Please install it first."
    exit 1
fi

# Set up virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/Update requirements
echo "📥 Checking dependencies..."
pip install -r requirements.txt --quiet

# Run the Streamlit app
echo "🌐 Launching Streamlit dashboard on port 8501..."
streamlit run app.py --server.port 8501
