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
    if len(sys.argv) < 4:
        print("Usage: python run_bot.py <leads_json> <message_template> <wait_time> [images_json]")
        sys.exit(1)

    leads_json = sys.argv[1]
    msg_template = sys.argv[2]
    wait_time = int(sys.argv[3])
    
    images = []
    if len(sys.argv) > 4:
        try:
            images = json.loads(sys.argv[4])
        except Exception as e:
            print(f"Error parsing images list: {e}")

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
                encoded_msg = requests.utils.quote(message) if message.strip() else ""
                driver.get(f"https://web.whatsapp.com/send?phone={phone}&text={encoded_msg}")
                
                # Wait for the chat to load successfully
                print("Waiting for chat to load...")
                chat_input = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.XPATH, '//div[@data-testid="conversation-text-input"] | //div[@contenteditable="true"][@role="textbox"]'))
                )
                time.sleep(2)  # Let dynamic overlays settle
                
                # 1. Send the text message if message is not empty
                text_sent = False
                if message.strip():
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
                        print(f"Sent text to {name} ({phone})")
                        result_entry["status"] = "success"
                        text_sent = True
                        time.sleep(2)  # Wait for message to register
                    else:
                        error_msg = "Could not find text send button"
                        print(error_msg)
                        result_entry["error"] = error_msg
                else:
                    # If no text is configured but we are sending images, set text_sent to True to allow image sending
                    if images:
                        text_sent = True
                        result_entry["status"] = "success"

                # 2. Upload and send images if configured
                if text_sent and images:
                    # Validate all image paths and resolve to absolute paths
                    abs_images = []
                    for img_path in images:
                        abs_path = os.path.abspath(img_path)
                        if os.path.exists(abs_path):
                            abs_images.append(abs_path)
                        else:
                            print(f"Image path not found: {abs_path}")
                            result_entry["error"] += f" | Image not found: {os.path.basename(abs_path)}"
                    
                    if abs_images:
                        print(f"Uploading {len(abs_images)} images at once...")
                        try:
                            # A. Locate the hidden file upload input element directly in the DOM (Attach click not needed)
                            image_input = None
                            input_selectors = [
                                '//input[@type="file" and contains(@accept, "image/")]',
                                '//input[@type="file" and contains(@accept, "image")]',
                                '//input[@accept="image/*,video/mp4,video/3gpp,video/quicktime"]',
                                '//input[@type="file"]'
                            ]
                            for xpath in input_selectors:
                                try:
                                    image_input = WebDriverWait(driver, 10).until(
                                        EC.presence_of_element_located((By.XPATH, xpath))
                                    )
                                    if image_input:
                                        print(f"Found file input using selector: {xpath}")
                                        break
                                except:
                                    continue
                                    
                            if not image_input:
                                raise Exception("Could not locate the file upload input element in the DOM.")
                            
                            # B. Send all absolute file paths joined by newline to upload them at once!
                            joined_paths = "\n".join(abs_images)
                            image_input.send_keys(joined_paths)
                            print("File paths sent to input element successfully.")
                            
                            # C. Wait for preview screen send button to be clickable and click it
                            preview_send_selectors = [
                                '//span[@data-testid="send"]',
                                '//span[@data-icon="send"]',
                                '//button[@aria-label="Send"]',
                                '//div[@data-testid="send"]',
                                '//div[@role="button" and @aria-label="Send"]',
                                '//span[@data-icon="send"]/ancestor::button',
                                '//span[@data-testid="send"]/ancestor::div[@role="button"]'
                            ]
                            
                            preview_send_btn = None
                            for preview_selector in preview_send_selectors:
                                try:
                                    preview_send_btn = WebDriverWait(driver, 15).until(
                                        EC.element_to_be_clickable((By.XPATH, preview_selector))
                                    )
                                    if preview_send_btn:
                                        print(f"Found preview send button using selector: {preview_selector}")
                                        break
                                except:
                                    continue
                            
                            if preview_send_btn:
                                time.sleep(2)  # Give the preview screen a moment to fully load
                                try:
                                    preview_send_btn.click()
                                except Exception:
                                    try:
                                        print("Normal click intercepted, trying JavaScript click...")
                                        driver.execute_script("arguments[0].click();", preview_send_btn)
                                    except Exception as js_err:
                                        print(f"JS click failed: {js_err}. Trying Keys.ENTER...")
                                        from selenium.webdriver.common.keys import Keys
                                        preview_send_btn.send_keys(Keys.ENTER)
                                    
                                print(f"Successfully sent {len(abs_images)} images to {name}.")
                                time.sleep(4)  # Wait for upload/send animation to complete
                            else:
                                raise Exception("Could not locate the Send button on the image preview screen.")
                                
                        except Exception as img_err:
                            error_msg = f"Error sending images: {str(img_err)}"
                            print(error_msg)
                            result_entry["error"] += f" | {error_msg}"
                
                # Wait dynamic delay between leads
                time.sleep(wait_time)
                
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
