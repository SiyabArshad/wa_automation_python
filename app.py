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

st.set_page_config(
    page_title="WA Automation Pro",
    layout="wide",
    page_icon="📲",
    initial_sidebar_state="expanded"
)

# --- Premium Custom Styling ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap');

    :root {
        --primary: #25D366;
        --primary-hover: #128C7E;
        --bg-dark: #0B0E11;
        --card-bg: rgba(22, 27, 34, 0.7);
        --text-main: #E6EDF3;
        --text-muted: #8B949E;
        --border: rgba(48, 54, 61, 0.5);
    }

    * {
        font-family: 'Inter', sans-serif !important;
    }

    /* Main Background */
    .stApp {
        background: radial-gradient(circle at top right, #1a2a21, #0b0e11 40%);
        color: var(--text-main);
    }

    /* Sidebar Glassmorphism */
    section[data-testid="stSidebar"] {
        background-color: rgba(13, 17, 23, 0.8) !important;
        backdrop-filter: blur(10px);
        border-right: 1px solid var(--border);
    }

    /* Header Styling */
    h1 {
        font-size: 2.8rem !important;
        font-weight: 800 !important;
        background: linear-gradient(135deg, #25D366 0%, #128C7E 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem !important;
    }
    
    h2, h3 {
        color: var(--text-main) !important;
        font-weight: 600 !important;
        letter-spacing: -0.5px;
    }

    /* Card Component */
    .custom-card {
        background: var(--card-bg);
        padding: 2rem;
        border-radius: 16px;
        border: 1px solid var(--border);
        backdrop-filter: blur(8px);
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 32px rgba(0,0,0,0.2);
    }

    /* Button Premium Styling */
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 3.8em;
        background: linear-gradient(135deg, #25D366 0%, #128C7E 100%) !important;
        color: white !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        border: none !important;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        box-shadow: 0 10px 20px rgba(37, 211, 102, 0.15);
    }
    
    .stButton>button:hover {
        transform: translateY(-4px) scale(1.02);
        box-shadow: 0 15px 35px rgba(37, 211, 102, 0.3);
        background: linear-gradient(135deg, #26e06c 0%, #15a393 100%) !important;
    }

    /* Form Inputs */
    .stTextInput>div>div>input, 
    .stTextArea>div>div>textarea, 
    .stSelectbox>div>div>div {
        background-color: rgba(13, 17, 23, 0.6) !important;
        color: white !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        padding: 12px !important;
        font-size: 1rem !important;
    }
    
    .stTextInput>div>div>input:focus, 
    .stTextArea>div>div>textarea:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 2px rgba(37, 211, 102, 0.2) !important;
    }

    /* Metrics Styling */
    [data-testid="stMetricValue"] {
        font-size: 2.2rem !important;
        font-weight: 800 !important;
        color: var(--primary) !important;
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: transparent;
    }

    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: var(--card-bg);
        border-radius: 10px 10px 0 0;
        padding: 0 20px;
        color: var(--text-muted);
    }

    .stTabs [aria-selected="true"] {
        background-color: var(--primary) !important;
        color: white !important;
    }

    /* Hide default Streamlit footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    ::-webkit-scrollbar-track {
        background: var(--bg-dark);
    }
    ::-webkit-scrollbar-thumb {
        background: #30363d;
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #484f58;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Header ---
st.markdown('<div style="text-align: center; padding: 2rem 0;">', unsafe_allow_html=True)
st.title("📲 WA Automation Pro")
st.markdown('<p style="color: var(--text-muted); font-size: 1.2rem; margin-top: -10px;">Enterprise WhatsApp Marketing Dashboard</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- Metrics Row ---
if 'leads_df' not in st.session_state:
    st.session_state.leads_df = None
if 'subdivisions' not in st.session_state:
    st.session_state.subdivisions = []

m_col1, m_col2, m_col3 = st.columns(3)
with m_col1:
    total_leads = len(st.session_state.leads_df) if st.session_state.leads_df is not None else 0
    st.metric("Total Leads", total_leads)
with m_col2:
    st.metric("Active Process", "Idle" if 'automation_running' not in st.session_state else "Running")
with m_col3:
    st.metric("System Health", "Optimal")

st.markdown("<br>", unsafe_allow_html=True)

# --- Sidebar / Configuration ---
with st.sidebar:
    st.markdown("### 🔑 Authentication")
    api_base_url = st.text_input("Backend URL", value="https://api.sanjeevanidesifoodhub.com")
    api_token = st.text_input("Bearer Token", type="password")
    tenant_name = st.text_input("Tenant", value="kitchen")
    
    st.markdown("<br>### ⚙️ Automation Settings", unsafe_allow_html=True)
    use_headless = st.checkbox("Run in Background", value=False)
    wait_time = st.slider("Delay (seconds)", 2, 10, 5)
    
    st.markdown("<br>### 🛠️ Maintenance", unsafe_allow_html=True)
    if st.button("🗑️ Reset Chrome Instance"):
        import subprocess
        try:
            subprocess.run(["pkill", "-f", "Google Chrome"], check=False)
            subprocess.run(["pkill", "-f", "chromedriver"], check=False)
            st.success("Environment cleared!")
        except:
            st.error("Cleanup failed.")

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

# --- Main Dashboard ---
tab1, tab2 = st.tabs(["📋 Lead Management", "✉️ Campaign Setup"])

with tab1:
    st.markdown('<div class="custom-card">', unsafe_allow_html=True)
    col_a, col_b = st.columns([1, 1])
    with col_a:
        st.markdown("### 📥 Data Sync")
        if st.button("🔄 REFRESH LEADS FROM API"):
            fetch_leads()
    
    if st.session_state.leads_df is not None:
        st.markdown("---")
        st.markdown("### 🔍 Filters")
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            selected_sub = st.selectbox("Subdivision", options=st.session_state.subdivisions if st.session_state.subdivisions else ["All"])
        with f_col2:
            search_term = st.text_input("Search anything...", placeholder="Name, Phone, City...")

        df_filtered = st.session_state.leads_df.copy()
        if selected_sub != "All":
            df_filtered = df_filtered[df_filtered['subdivision'] == selected_sub]
        if search_term:
            df_filtered = df_filtered[
                df_filtered['name'].str.contains(search_term, case=False, na=False) |
                df_filtered['contact'].str.contains(search_term, case=False, na=False) |
                df_filtered['city'].str.contains(search_term, case=False, na=False)
            ]

        st.markdown(f"**Showing {len(df_filtered)} matching leads**")
        
        df_display = df_filtered[['id', 'name', 'contact', 'city', 'owner1', 'subdivision']].copy()
        df_display['Select'] = False
        
        edited_df = st.data_editor(
            df_display,
            column_config={
                "Select": st.column_config.CheckboxColumn("Send?", default=False),
                "contact": "Phone",
                "name": "Customer",
                "subdivision": "Area"
            },
            disabled=['id', 'name', 'contact', 'city', 'owner1', 'subdivision'],
            hide_index=True,
            use_container_width=True
        )
        st.session_state.selected_leads = edited_df[edited_df['Select'] == True]
    else:
        st.info("👈 Please enter your token in the sidebar and sync data.")
    st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    if 'selected_leads' in st.session_state and not st.session_state.selected_leads.empty:
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        st.markdown(f"### 🚀 Ready for Broadcast")
        st.info(f"Targeting **{len(st.session_state.selected_leads)}** customers")
        
        msg_template = st.text_area(
            "Message Content", 
            height=200,
            value="Hello {name},\n\nThis is from Sanjeevani Desi Food Hub! 🥭\nWe have some fresh updates for you.\n\nRegards,\nAdmin",
            help="Tip: Use {name} to personalize!"
        )
        
        if st.button("🔥 START BROADCAST"):
            import subprocess
            import tempfile
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            with st.spinner("Initializing automation engine..."):
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                    st.session_state.selected_leads.to_json(f.name)
                    temp_leads_path = f.name
                
                process = subprocess.Popen(
                    [sys.executable, "run_bot.py", temp_leads_path, msg_template, str(wait_time)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True
                )
                
                for line in process.stdout:
                    status_text.info(line.strip())
                
                process.wait()
                
            if process.returncode == 0:
                st.balloons()
                st.success("✅ Campaign finished successfully!")
            else:
                st.error("❌ Process interrupted. Check console logs.")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning("⚠️ Go to 'Lead Management' and select some leads first.")
