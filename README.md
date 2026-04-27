# WhatsApp Automation Bot (Standalone)

A professional WhatsApp automation tool built with Streamlit and Selenium (Undetected Chromedriver).

## 🚀 Getting Started

### 1. Requirements
- Python 3.8 or higher
- Google Chrome browser installed

### 2. Installation
Open your terminal in this directory and run:
```bash
pip install -r requirements.txt
```

### 3. Running the App
```bash
streamlit run app.py
```

## 🛠️ How to use
1. Get your **Bearer Token** from your Admin Panel (check browser network logs or copy it if you have a way).
2. Enter the **API Base URL** and **Token** in the sidebar.
3. Click **Load Leads** to fetch your marketing database.
4. Select the customers you want to message from the table.
5. Edit your message template (use `{name}` for personalization).
6. Click **Launch Automation**.
7. A browser window will open. If it's your first time, **scan the QR code** with your phone. The app will save your session in the `chrome_profile` folder so you don't have to scan every time.

## ⚠️ Important Note
This tool uses browser automation. Please use it responsibly and follow WhatsApp's anti-spam policies to avoid your number being flagged.
