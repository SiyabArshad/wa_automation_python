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
    /* Dark Theme Core */
    .stApp {
        background-color: #0f1116;
        color: #e6edf3;
    }
    
    /* Header Styling */
    h1 {
        color: #25D366 !important;
        font-weight: 800 !important;
        letter-spacing: -1px;
    }
    
    /* Button Premium Styling */
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 3.5em;
        background: linear-gradient(135deg, #25D366 0%, #128C7E 100%);
        color: white !important;
        font-weight: 700;
        border: none;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        text-transform: uppercase;
        letter-spacing: 1px;
        box-shadow: 0 4px 15px rgba(37, 211, 102, 0.2);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(37, 211, 102, 0.4);
        border: none;
        color: white !important;
    }

    /* Input & Area Styling */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div>div {
        background-color: #161b22 !important;
        color: #e6edf3 !important;
        border: 1px solid #30363d !important;
        border-radius: 8px !important;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0d1117;
        border-right: 1px solid #30363d;
    }
    
    /* Data Editor / Table Styling */
    div[data-testid="stTable"] {
        background-color: #161b22;
        border-radius: 10px;
    }

    /* Alert Styling */
    .stAlert {
        border-radius: 12px;
        border: 1px solid #30363d;
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
if 'subdivisions' not in st.session_state:
    st.session_state.subdivisions = []

def fetch_subdivisions():
    if not api_token: return
    headers = {"Authorization": f"Bearer {api_token}", "x-tenant-name": tenant_name}
    try:
        url = f"{api_base_url}/api/marketing-addresses/subdivisions"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            st.session_state.subdivisions = ["All"] + response.json()
    except: pass

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
                # Also refresh subdivisions
                fetch_subdivisions()
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
    
    filter_col1, filter_col2 = st.columns(2)
    
    with filter_col1:
        # Subdivision Filter
        selected_sub = st.selectbox("Filter by Subdivision", options=st.session_state.subdivisions if st.session_state.subdivisions else ["All"])
    
    with filter_col2:
        # Filter/Search in local data
        search_term = st.text_input("Search (Name, Phone, City)", "")
    
    df_filtered = st.session_state.leads_df.copy()
    
    # Apply Subdivision Filter
    if selected_sub != "All":
        df_filtered = df_filtered[df_filtered['subdivision'] == selected_sub]
        
    # Apply Search Filter
    if search_term:
        df_filtered = df_filtered[
            df_filtered['name'].str.contains(search_term, case=False, na=False) |
            df_filtered['contact'].str.contains(search_term, case=False, na=False) |
            df_filtered['city'].str.contains(search_term, case=False, na=False)
        ]

    # Selection Table
    df_display = df_filtered[['id', 'name', 'contact', 'city', 'owner1', 'subdivision']].copy()
    df_display['Select'] = False
    
    edited_df = st.data_editor(
        df_display,
        column_config={
            "Select": st.column_config.CheckboxColumn("Send?", default=False),
            "contact": "Phone Number",
            "name": "Customer Name",
            "subdivision": "Subdivision"
        },
        disabled=['id', 'name', 'contact', 'city', 'owner1', 'subdivision'],
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
