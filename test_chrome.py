from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

print("🔍 Testing simple Chrome launch...")
try:
    options = Options()
    # options.add_argument("--headless") # Optional
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    print("✅ Success! Browser opened.")
    driver.get("https://www.google.com")
    time.sleep(5)
    driver.quit()
    print("✅ Browser closed.")
except Exception as e:
    print(f"❌ Failed: {e}")
