import sys
import io

# Fix for Windows Unicode errors
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
import os
import json
import time
import requests
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def main():
    if len(sys.argv) < 3:
        print("Usage: python run_bot.py <leads_json> <message_template> <wait_time>")
        sys.exit(1)

    leads_json = sys.argv[1]
    msg_template = sys.argv[2]
    wait_time = int(sys.argv[3])

    leads = pd.read_json(leads_json)
    
    options = Options()
    # Use a location in Documents to avoid project-folder permission issues on macOS
    profile_dir = os.path.expanduser("~/Documents/whatsapp_automation_profile")
    if not os.path.exists(profile_dir):
        os.makedirs(profile_dir)
    options.add_argument(f"--user-data-dir={profile_dir}")
    
    # Standard stability flags for macOS
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-infobars")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--no-first-run")
    
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    print(f"Using persistent profile: {profile_dir}")
    print("Launching Browser Engine...")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    results = []
    try:
        print("Opening WhatsApp Web...")
        driver.get("https://web.whatsapp.com")
        
        # Try to dismiss initial popups if they appear
        try:
            time.sleep(2)
            alert = driver.switch_to.alert
            alert.accept()
            print("Dismissed system alert.")
        except:
            pass

        print("Waiting for login (Please scan QR code if not logged in)...")
        WebDriverWait(driver, 120).until(
            EC.presence_of_element_located((By.XPATH, '//div[@data-testid="chat-list"]'))
        )
        print("Logged in!")
        
        total = len(leads)
        for i, (idx, row) in enumerate(leads.iterrows()):
            record_id = row.get('id', 'N/A')
            name = row.get('name') or row.get('owner1') or "Customer"
            phone = "".join(filter(str.isdigit, str(row.get('contact', ''))))
            # If number is 10 digits, assume US and prepend '1'
            if len(phone) == 10: 
                phone = "1" + phone
            
            message = msg_template.replace("{name}", name)
            print(f"[{i+1}/{total}] Sending to {name} ({phone})...")
            
            result_entry = {
                "id": record_id,
                "name": name,
                "phone": phone,
                "sent_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "status": "failed",
                "message_text": message,
                "error": ""
            }

            try:
                encoded_msg = requests.utils.quote(message)
                driver.get(f"https://web.whatsapp.com/send?phone={phone}&text={encoded_msg}")
                
                # Try multiple common WhatsApp send button selectors
                send_selectors = [
                    '//span[@data-icon="send"]',
                    '//button[@aria-label="Send"]',
                    '//span[@data-testid="send"]',
                    '//button/span[@data-icon="send"]'
                ]
                
                send_btn = None
                for selector in send_selectors:
                    try:
                        send_btn = WebDriverWait(driver, 15).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        if send_btn: break
                    except:
                        continue
                
                if send_btn:
                    time.sleep(1)
                    send_btn.click()
                    print(f"Sent to {phone}")
                    result_entry["status"] = "success"
                    time.sleep(wait_time)
                else:
                    error_msg = "Could not find send button"
                    print(error_msg)
                    result_entry["error"] = error_msg
            except Exception as e:
                error_msg = str(e)
                print(f"Error sending to {phone}: {error_msg}")
                result_entry["error"] = error_msg
            
            results.append(result_entry)
            
        print("Automation completed!")
        
    except Exception as ex:
        print(f"Error: {ex}")
    finally:
        # Save results to a file
        results_path = leads_json.replace(".json", "_results.json")
        try:
            with open(results_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"REPORT_PATH:{results_path}")
        except Exception as save_err:
            print(f"Failed to save report: {save_err}")

        print("Closing browser in 5 seconds...")
        time.sleep(5)
        driver.quit()

if __name__ == "__main__":
    main()
