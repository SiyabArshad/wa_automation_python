import streamlit as st
import pandas as pd
import requests
import time
import os
import json
import sys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium_stealth import stealth
from selenium.webdriver.common.keys import Keys
from dotenv import load_dotenv

# Load local environment if exists
load_dotenv()

st.set_page_config(page_title="WA Automation Pro", layout="wide", page_icon="📲")

# --- Custom Styling ---
st.markdown("""
    <style>
    .main {
        background-color: #f5f7f9;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #25D366;
        color: white;
    }
    .stButton>button:hover {
        background-color: #128C7E;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📲 WhatsApp Marketing Automation Pro")
st.markdown("---")

# --- Sidebar / Configuration ---
st.sidebar.header("🔑 API Configuration")
api_base_url = st.sidebar.text_input("Backend API URL", value="https://api.sanjeevanidesifoodhub.com")
api_token = st.sidebar.text_input("Bearer Token", type="password", help="Enter your admin token from the web app")
tenant_name = st.sidebar.text_input("Tenant", value="kitchen")

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Browser Settings")
use_headless = st.sidebar.checkbox("Run Headless (Background)", value=False)
wait_time = st.sidebar.slider("Delay between messages (sec)", 2, 10, 5)

st.sidebar.markdown("---")
st.sidebar.header("🛠️ Maintenance")
if st.sidebar.button("🗑️ Force Clean Browser"):
    import subprocess
    try:
        # Kill Chrome and Driver on Mac/Linux
        subprocess.run(["pkill", "-f", "Google Chrome"], check=False)
        subprocess.run(["pkill", "-f", "chromedriver"], check=False)
        st.sidebar.success("Closed all Chrome processes. Try launching now.")
    except Exception as e:
        st.sidebar.error(f"Cleanup failed: {e}")

# Session State
if 'leads_df' not in st.session_state:
    st.session_state.leads_df = None

def fetch_leads():
    if not api_token:
        st.error("Please enter a Bearer Token.")
        return
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "x-tenant-name": tenant_name
    }
    
    try:
        with st.spinner("Fetching data from marketing API..."):
            url = f"{api_base_url}/api/marketing-addresses/all-details?limit=5000"
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json().get('data', [])
                if not data:
                    st.warning("No data returned from API.")
                    return
                
                df = pd.DataFrame(data)
                # Filter for phone numbers
                df = df[df['contact_type'] == 'phone']
                st.session_state.leads_df = df
                st.success(f"Successfully loaded {len(df)} leads.")
            else:
                st.error(f"API Error: {response.status_code}")
    except Exception as e:
        st.error(f"Connection Error: {str(e)}")

# --- Main Logic ---
col1, col2 = st.columns([1, 2])

with col1:
    if st.button("📥 Load Leads from API"):
        fetch_leads()

if st.session_state.leads_df is not None:
    st.subheader("📋 Lead Selection & Message Content")
    
    # Filter/Search in local data
    search_term = st.text_input("Search in loaded data", "")
    df_filtered = st.session_state.leads_df.copy()
    if search_term:
        df_filtered = df_filtered[
            df_filtered['name'].str.contains(search_term, case=False, na=False) |
            df_filtered['contact'].str.contains(search_term, case=False, na=False) |
            df_filtered['city'].str.contains(search_term, case=False, na=False)
        ]

    # Selection Table
    df_display = df_filtered[['id', 'name', 'contact', 'city', 'owner1']].copy()
    df_display['Select'] = False
    
    edited_df = st.data_editor(
        df_display,
        column_config={
            "Select": st.column_config.CheckboxColumn("Send?", default=False),
            "contact": "Phone Number",
            "name": "Customer Name"
        },
        disabled=['id', 'name', 'contact', 'city', 'owner1'],
        hide_index=True,
        use_container_width=True
    )

    selected_leads = edited_df[edited_df['Select'] == True]
    
    st.markdown(f"**Target Count:** `{len(selected_leads)}` leads selected.")

    # Message Area
    st.markdown("### ✉️ Message Template")
    msg_template = st.text_area(
        "Edit your message", 
        height=150,
        value="Hello {name},\n\nThis is from Sanjeevani Desi Food Hub! 🥭\nWe have some fresh updates for you.\n\nRegards,\nAdmin",
        help="Use {name} to personalize the message."
    )

    if st.button("🚀 LAUNCH AUTOMATION"):
        if len(selected_leads) == 0:
            st.error("Select at least one lead to start.")
        else:
            # --- Automation Execution via Separate Process ---
            import subprocess
            import tempfile
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            with st.spinner("🚀 Launching Automation Process..."):
                # Save leads to temp file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                    selected_leads.to_json(f.name)
                    temp_leads_path = f.name
                
                # Start the process
                process = subprocess.Popen(
                    [sys.executable, "run_bot.py", temp_leads_path, msg_template, str(wait_time)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True
                )
                
                # Monitor output
                for line in process.stdout:
                    status_text.info(line.strip())
                    if "Sending to" in line:
                        # Simple progress estimate
                        pass 
                
                process.wait()
                
            if process.returncode == 0:
                st.balloons()
                st.success("✅ Automation completed successfully!")
            else:
                st.error("❌ Automation process failed. Check the logs above.")

else:
    st.info("👈 Enter your Bearer Token and click 'Load Leads' to begin.")
