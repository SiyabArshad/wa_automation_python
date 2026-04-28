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
    initial_sidebar_state="expanded"
)

# --- Clean Business Styling ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

    :root {
        --primary: #25D366;
        --primary-dark: #128C7E;
        --bg-light: #F8FAFC;
        --card-bg: #FFFFFF;
        --text-main: #1E293B;
        --text-muted: #64748B;
        --border: #E2E8F0;
    }

    * {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }

    /* Main Background */
    .stApp {
        background-color: var(--bg-light);
        color: var(--text-main);
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid var(--border);
    }

    /* Header Styling */
    h1 {
        font-size: 3rem !important;
        font-weight: 800 !important;
        color: var(--text-main) !important;
        letter-spacing: -1.5px !important;
        margin-bottom: 0rem !important;
    }
    
    h2, h3 {
        color: var(--text-main) !important;
        font-weight: 700 !important;
        letter-spacing: -0.5px;
    }

    /* Card Component */
    .custom-card {
        background: var(--card-bg);
        padding: 2.5rem;
        border-radius: 20px;
        border: 1px solid var(--border);
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }

    /* Button Premium Styling */
    .stButton>button {
        width: 100%;
        border-radius: 14px;
        height: 4em;
        background-color: var(--primary) !important;
        color: white !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        border: none !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 14px 0 rgba(37, 211, 102, 0.39);
    }
    
    .stButton>button:hover {
        background-color: var(--primary-dark) !important;
        box-shadow: 0 6px 20px rgba(37, 211, 102, 0.23);
        transform: translateY(-2px);
    }

    /* Form Inputs */
    .stTextInput>div>div>input, 
    .stTextArea>div>div>textarea, 
    .stSelectbox>div>div>div {
        background-color: #FFFFFF !important;
        color: var(--text-main) !important;
        border: 1.5px solid var(--border) !important;
        border-radius: 12px !important;
        padding: 14px !important;
        font-size: 1rem !important;
    }
    
    .stTextInput>div>div>input:focus, 
    .stTextArea>div>div>textarea:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 4px rgba(37, 211, 102, 0.1) !important;
    }

    /* Metrics Styling */
    [data-testid="stMetric"] {
        background: white;
        padding: 1.5rem;
        border-radius: 16px;
        border: 1px solid var(--border);
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }

    [data-testid="stMetricValue"] {
        font-size: 2.5rem !important;
        font-weight: 800 !important;
        color: var(--primary-dark) !important;
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        padding: 8px;
        background-color: #F1F5F9;
        border-radius: 16px;
        margin-bottom: 20px;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        padding: 8px 24px;
        color: var(--text-muted);
        border: none !important;
    }

    .stTabs [aria-selected="true"] {
        background-color: white !important;
        color: var(--primary-dark) !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }

    /* Hide default Streamlit footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- Header ---
st.markdown('<div style="text-align: center; padding: 2rem 0;">', unsafe_allow_html=True)
st.title("WA Automation Pro")
st.markdown('<p style="color: var(--text-muted); font-size: 1.2rem; margin-top: -10px;">Enterprise WhatsApp Marketing Dashboard</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- Session State ---
if 'leads_df' not in st.session_state:
    st.session_state.leads_df = None
if 'subdivisions' not in st.session_state:
    st.session_state.subdivisions = []

st.markdown("<br>", unsafe_allow_html=True)

# --- Sidebar / Configuration ---
with st.sidebar:
    st.markdown("### Authentication")
    api_base_url = st.text_input("Backend URL", value="https://api.sanjeevanidesifoodhub.com")
    api_token = st.text_input("Bearer Token", type="password")
    tenant_name = st.text_input("Tenant", value="kitchen")
    
    st.markdown("<br>### Automation Settings", unsafe_allow_html=True)
    use_headless = st.checkbox("Run in Background", value=False)
    wait_time = st.slider("Delay (seconds)", 2, 10, 5)
    
    st.markdown("<br>### Maintenance", unsafe_allow_html=True)
    if st.button("Reset Chrome Instance"):
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
tab1, tab2 = st.tabs(["Lead Management", "Campaign Setup"])

with tab1:
    col_a, col_b = st.columns([1, 1])
    with col_a:
        st.markdown("### Data Sync")
        if st.button("REFRESH LEADS FROM API"):
            fetch_leads()
    
    if st.session_state.leads_df is not None:
        st.markdown("---")
        st.markdown("### Filters")
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
        st.info("Please enter your token in the sidebar and sync data.")

with tab2:
    if 'selected_leads' in st.session_state and not st.session_state.selected_leads.empty:
        st.markdown(f"### Ready for Broadcast")
        st.info(f"Targeting **{len(st.session_state.selected_leads)}** customers")
        
        msg_template = st.text_area(
            "Message Content", 
            height=200,
            value="Hello {name},\n\nThis is from Sanjeevani Desi Food Hub!\nWe have some fresh updates for you.\n\nRegards,\nAdmin",
            help="Tip: Use {name} to personalize!"
        )
        
        if st.button("START BROADCAST"):
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
                st.success("Campaign finished successfully!")
            else:
                st.error("Process interrupted. Check console logs.")
        st.markdown('Campaign Setup')
    else:
        st.warning("Please go to 'Lead Management' and select some leads first.")
