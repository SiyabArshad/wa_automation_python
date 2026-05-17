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
if 'selected_ids' not in st.session_state:
    st.session_state.selected_ids = set()

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
                st.session_state.selected_ids = set()
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

        df_display = df_filtered[['id', 'name', 'contact', 'city', 'owner1', 'subdivision']].copy()
        
        # Coerce IDs to string to avoid comparison mismatch issues
        df_display['id'] = df_display['id'].astype(str)
        
        # Populate initial checkbox state based on current global selections
        df_display['Select'] = df_display['id'].isin(st.session_state.selected_ids)
        
        # Selection Action Controls
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
        with col_btn1:
            if st.button("✅ Select All Filtered"):
                st.session_state.selected_ids.update(df_display['id'].tolist())
                st.rerun()
        with col_btn2:
            if st.button("❌ Deselect All Filtered"):
                st.session_state.selected_ids.difference_update(df_display['id'].tolist())
                st.rerun()
        with col_btn3:
            if st.button("🧹 Clear All Selections"):
                st.session_state.selected_ids.clear()
                st.rerun()

        # Display Selected Counter for user convenience
        num_selected_filtered = df_display['id'].isin(st.session_state.selected_ids).sum()
        st.markdown(
            f"**Showing {len(df_filtered)} matching leads** (Selected in this view: **{num_selected_filtered}** | Total selected: **{len(st.session_state.selected_ids)}**)"
        )
        
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
            use_container_width=True,
            key="leads_editor"
        )
        
        # Sync changes from the editor back to the session state selected_ids
        if edited_df is not None:
            for _, row in edited_df.iterrows():
                row_id = str(row['id'])
                if row['Select']:
                    st.session_state.selected_ids.add(row_id)
                else:
                    st.session_state.selected_ids.discard(row_id)

        # Update the selected_leads for Broadcast using selected_ids
        # We query the original leads_df to keep it accurate, complete, and persistent across filters
        if st.session_state.leads_df is not None:
            st.session_state.selected_leads = st.session_state.leads_df[
                st.session_state.leads_df['id'].astype(str).isin(st.session_state.selected_ids)
            ]
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
        
        st.markdown("<br>### 🖼️ Media Attachments (Optional)", unsafe_allow_html=True)
        
        default_downloads = os.path.expanduser("~/Downloads")
        downloads_dir = st.text_input("Downloads Folder Path", value=default_downloads, help="Specify the folder where your promotional images are located.")
        
        available_images = []
        if os.path.exists(downloads_dir):
            try:
                import glob
                extensions = ['*.png', '*.jpg', '*.jpeg', '*.webp', '*.gif', '*.PNG', '*.JPG', '*.JPEG']
                for ext in extensions:
                    available_images.extend(glob.glob(os.path.join(downloads_dir, ext)))
                available_images = sorted([os.path.basename(f) for f in available_images])
            except Exception as e:
                st.error(f"Error scanning folder: {e}")
        
        col_img1, col_img2 = st.columns([1, 1])
        with col_img1:
            selected_filenames = st.multiselect(
                "Select Images from Downloads", 
                options=available_images,
                help="Choose one or multiple image files to send."
            )
        with col_img2:
            custom_images_input = st.text_input(
                "Or manually enter image names (comma-separated)",
                placeholder="e.g. image1.jpg, offer.png",
                help="Enter filename(s) if not showing in the list."
            )
            
        selected_image_paths = []
        for fname in selected_filenames:
            full_path = os.path.join(downloads_dir, fname)
            if os.path.exists(full_path) and full_path not in selected_image_paths:
                selected_image_paths.append(full_path)
                
        if custom_images_input:
            manual_names = [name.strip() for name in custom_images_input.split(",") if name.strip()]
            for name in manual_names:
                full_path = name if os.path.isabs(name) else os.path.join(downloads_dir, name)
                if os.path.exists(full_path):
                    if full_path not in selected_image_paths:
                        selected_image_paths.append(full_path)
                else:
                    st.warning(f"⚠️ Image not found: {name} (Checked: {full_path})")
                    
        if selected_image_paths:
            st.markdown("##### 📌 Selected Attachments:")
            for path in selected_image_paths:
                st.markdown(f"- `{os.path.basename(path)}` &nbsp; *({os.path.abspath(path)})*")
            st.markdown("<br>", unsafe_allow_html=True)
        
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
                
                # Serialize the image paths list as JSON string
                images_json = json.dumps(selected_image_paths)
                
                process = subprocess.Popen(
                    [sys.executable, "run_bot.py", temp_leads_path, msg_template, str(wait_time), images_json],
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
