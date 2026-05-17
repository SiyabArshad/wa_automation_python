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
if 'selected_lead_ids' not in st.session_state:
    st.session_state.selected_lead_ids = set()
if 'loaded_file_name' not in st.session_state:
    st.session_state.loaded_file_name = None

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
    st.markdown("### Lead Data Source")
    data_source = st.radio(
        "Choose how you want to load your leads:",
        ["API Integration", "Excel / CSV File Upload"],
        horizontal=True
    )
    
    if data_source == "API Integration":
        # Clear uploaded file states if switching to API to avoid crossover data pollution
        if st.session_state.loaded_file_name is not None:
            st.session_state.leads_df = None
            st.session_state.loaded_file_name = None
            st.session_state.selected_lead_ids = set()
            
        col_a, col_b = st.columns([1, 1])
        with col_a:
            st.markdown("### Data Sync")
            if st.button("REFRESH LEADS FROM API"):
                fetch_leads()
    else:
        st.markdown("### Upload Spreadsheets (Excel / CSV)")
        
        # If a file has already been parsed and loaded successfully, show a clean success card instead of uploader
        if st.session_state.loaded_file_name is not None:
            st.success(f"📂 Successfully loaded **{len(st.session_state.leads_df)}** leads from `{st.session_state.loaded_file_name}`.")
            if st.button("🔄 Upload a Different File / Reset", use_container_width=True):
                st.session_state.leads_df = None
                st.session_state.loaded_file_name = None
                st.session_state.selected_lead_ids = set()
                try:
                    st.rerun()
                except AttributeError:
                    st.experimental_rerun()
        else:
            uploaded_file = st.file_uploader(
                "Upload your .xlsx, .xls, or .csv file",
                type=["csv", "xlsx", "xls"],
                help="Your file should have a column containing the phone numbers (formatted with +1 or local digits)."
            )
            
            if uploaded_file is not None:
                try:
                    # Read the file
                    file_name = uploaded_file.name.lower()
                    if file_name.endswith('.csv'):
                        df_raw = pd.read_csv(uploaded_file)
                    else:
                        df_raw = pd.read_excel(uploaded_file)
                    
                    if df_raw.empty:
                        st.error("Uploaded file is empty.")
                    else:
                        st.success(f"Loaded {len(df_raw)} raw rows from {uploaded_file.name}.")
                        
                        columns = list(df_raw.columns)
                        
                        # Smart defaults: name col (1st column), phone col (3rd column / index 2)
                        default_name_idx = 0
                        for idx, c in enumerate(columns):
                            if "name" in str(c).lower():
                                default_name_idx = idx
                                break
                                
                        default_phone_idx = min(2, len(columns) - 1) if len(columns) >= 3 else 0
                        for idx, c in enumerate(columns):
                            if "phone" in str(c).lower() or "contact" in str(c).lower() or "mobile" in str(c).lower():
                                default_phone_idx = idx
                                break
                        
                        st.markdown("#### Map Excel/CSV Columns")
                        col_map1, col_map2 = st.columns(2)
                        with col_map1:
                            name_col = st.selectbox(
                                "Name Column (used for {name} template replacement)",
                                options=columns,
                                index=default_name_idx
                            )
                        with col_map2:
                            phone_col = st.selectbox(
                                "Phone Number Column (contains formatted numbers)",
                                options=columns,
                                index=default_phone_idx
                            )
                        
                        if st.button("PROCEED WITH UPLOADED FILE", use_container_width=True):
                            # Construct standardized DataFrame safely with lists to completely bypass custom Pandas indexes
                            standardized_df = pd.DataFrame({
                                'id': [f"file_{i}" for i in range(len(df_raw))],
                                'name': df_raw[name_col].astype(str).tolist(),
                                'contact': df_raw[phone_col].astype(str).tolist(),
                                'city': df_raw['city'].astype(str).tolist() if 'city' in df_raw.columns else ["N/A"] * len(df_raw),
                                'owner1': df_raw[name_col].astype(str).tolist(),
                                'subdivision': ["Uploaded File"] * len(df_raw)
                            })
                            
                            # Filter for valid rows (ensure contact number is present)
                            standardized_df = standardized_df[standardized_df['contact'].str.strip() != ""]
                            
                            st.session_state.leads_df = standardized_df
                            st.session_state.subdivisions = ["All", "Uploaded File"]
                            st.session_state.selected_lead_ids = set() # Clear previous selections
                            st.session_state.loaded_file_name = uploaded_file.name
                            
                            try:
                                st.rerun()
                            except AttributeError:
                                st.experimental_rerun()
                except Exception as e:
                    st.error(f"Error reading file: {str(e)}")
    
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
        
        # Select / Deselect All Matching Leads
        col_sel1, col_sel2 = st.columns(2)
        with col_sel1:
            if st.button("✅ Select All Matching", use_container_width=True):
                for lead_id in df_filtered['id']:
                    st.session_state.selected_lead_ids.add(lead_id)
                try:
                    st.rerun()
                except AttributeError:
                    st.experimental_rerun()
        with col_sel2:
            if st.button("❌ Deselect All Matching", use_container_width=True):
                for lead_id in df_filtered['id']:
                    st.session_state.selected_lead_ids.discard(lead_id)
                try:
                    st.rerun()
                except AttributeError:
                    st.experimental_rerun()
        
        df_display = df_filtered[['id', 'name', 'contact', 'city', 'owner1', 'subdivision']].copy()
        # Initialize default selection state from the session state set
        df_display['Select'] = df_display['id'].apply(lambda x: x in st.session_state.selected_lead_ids)
        
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
        
        # Sync the manual editor selections back to our global selected set
        for _, row in edited_df.iterrows():
            lead_id = row['id']
            if row['Select']:
                st.session_state.selected_lead_ids.add(lead_id)
            else:
                st.session_state.selected_lead_ids.discard(lead_id)
                
        # Update the selected_leads DataFrame for campaign broadcast mapping
        st.session_state.selected_leads = st.session_state.leads_df[st.session_state.leads_df['id'].isin(st.session_state.selected_lead_ids)]
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
            
            if 'campaign_finished' not in st.session_state:
                st.session_state.campaign_finished = False
            if 'last_report_path' not in st.session_state:
                st.session_state.last_report_path = None

            with st.spinner("Initializing automation engine..."):
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                    st.session_state.selected_leads.to_json(f.name)
                    temp_leads_path = f.name
                
                process = subprocess.Popen(
                    [sys.executable, "run_bot.py", temp_leads_path, msg_template, str(wait_time)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding='utf-8'
                )
                
                report_path = None
                for line in process.stdout:
                    clean_line = line.strip()
                    if "REPORT_PATH:" in clean_line:
                        report_path = clean_line.split("REPORT_PATH:")[1]
                    else:
                        status_text.info(clean_line)
                
                process.wait()
                
            if process.returncode == 0:
                st.session_state.campaign_finished = True
                st.session_state.last_report_path = report_path
                st.balloons()
                st.success("Campaign finished successfully!")
            else:
                st.error("Process interrupted. Check console logs.")

        # Persistent Report Display
        if st.session_state.get('campaign_finished') and st.session_state.get('last_report_path'):
            report_path = st.session_state.last_report_path
            if os.path.exists(report_path):
                with open(report_path, 'r', encoding='utf-8') as f:
                    report_data = json.load(f)
                
                st.session_state.campaign_report = pd.DataFrame(report_data)
                st.markdown("---")
                st.markdown("### 📊 Campaign Report")
                st.dataframe(st.session_state.campaign_report, use_container_width=True)
                
                # Export options
                col_ex1, col_ex2, col_ex3 = st.columns(3)
                with col_ex1:
                    csv = st.session_state.campaign_report.to_csv(index=False).encode('utf-8')
                    st.download_button("📥 Download CSV Report", csv, "campaign_report.csv", "text/csv", key='dl-csv')
                with col_ex2:
                    json_str = st.session_state.campaign_report.to_json(orient='records', indent=2).encode('utf-8')
                    st.download_button("📥 Download JSON Report", json_str, "campaign_report.json", "application/json", key='dl-json')
                with col_ex3:
                    if st.button("🔄 Sync to Database", key='sync-db-btn'):
                        # Prepare full results for syncing
                        results_to_sync = []
                        for _, row in st.session_state.campaign_report.iterrows():
                            rid = row.get('id')
                            if not rid or rid == 'N/A': continue
                            results_to_sync.append({"id": rid, "status": row['status'], "error": row['error'] if row['status'] == 'failed' else ""})
                        
                        if not results_to_sync:
                            st.warning("No valid records to sync.")
                        else:
                            try:
                                headers = {"Authorization": f"Bearer {api_token}", "x-tenant-name": tenant_name, "Content-Type": "application/json"}
                                sync_url = f"{api_base_url}/api/marketing-addresses/track-sends"
                                res = requests.post(sync_url, headers=headers, json={"results": results_to_sync})
                                if res.status_code == 200:
                                    st.success(f"Successfully synced {len(results_to_sync)} records!")
                                else:
                                    st.error(f"Sync failed: {res.status_code}")
                            except Exception as e:
                                st.error(f"Sync error: {str(e)}")
        st.markdown('Campaign Setup')
    else:
        st.warning("Please go to 'Lead Management' and select some leads first.")
