import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def run_whatsapp_automation(selected_leads, msg_template, wait_time, status_callback, progress_callback):
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = None
    try:
        status_callback("🌐 Launching Browser Engine...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

        status_callback("⚠️ Opening WhatsApp Web. Please scan QR code if prompted.")
        driver.get("https://web.whatsapp.com")
        
        # Wait for login (max 2 mins)
        WebDriverWait(driver, 120).until(
            EC.presence_of_element_located((By.XPATH, '//div[@data-testid="chat-list"]'))
        )
        status_callback("✅ Logged in! Starting message sequence...")
        
        total = len(selected_leads)
        for i, (idx, row) in enumerate(selected_leads.iterrows()):
            name = row['name'] or row['owner1'] or "Customer"
            phone = "".join(filter(str.isdigit, str(row['contact'])))
            # If number is 10 digits, assume US and prepend '1'
            if len(phone) == 10: 
                phone = "1" + phone
            
            message = msg_template.replace("{name}", name)
            status_callback(f"[{i+1}/{total}] Sending to {name} ({phone})...")
            
            # Encode message for URL
            encoded_msg = requests.utils.quote(message)
            driver.get(f"https://web.whatsapp.com/send?phone={phone}&text={encoded_msg}")
            
            try:
                # Wait for send button
                send_btn = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.XPATH, '//span[@data-icon="send"]'))
                )
                time.sleep(1)
                send_btn.click()
                time.sleep(wait_time)
            except Exception as e:
                status_callback(f"❌ Failed to send to {phone}. Skipping...")
            
            progress_callback((i + 1) / total)
        
        return True, "Automation completed successfully!"
        
    except Exception as ex:
        return False, str(ex)
    finally:
        if driver:
            time.sleep(5)
            driver.quit()
