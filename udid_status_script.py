import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# === CONFIGURATION FROM ENV ===
MOBILE_NUMBER = os.getenv("MOBILE_NUMBER")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_telegram_message(token, chat_id, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    response = requests.post(url, data=data)
    if not response.ok:
        print("Telegram Error:", response.text)
    return response.ok

# === Setup Headless Chrome WebDriver ===
options = Options()
options.add_argument('--headless')  # Headless mode for CI
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--window-size=1920,1080')

driver = webdriver.Chrome(options=options)
driver.implicitly_wait(10)

try:
    # Step 1: Open the website
    driver.get("https://swavlambancard.gov.in/track-your-application")

    # Step 2: Select the "Mobile Number" radio option
    driver.find_element(By.ID, "cat-mobile").click()

    # Step 3: Enter the mobile number
    input_box = driver.find_element(By.CSS_SELECTOR, 'input[formcontrolname="mobile"]')
    input_box.send_keys(MOBILE_NUMBER)

    # Step 4: Click the Submit button
    submit_btn = driver.find_element(By.CSS_SELECTOR, 'input[type="submit"][value="Submit"]')
    submit_btn.click()

    # Step 5: Extract table content
    time.sleep(3)  # Wait for table to load
    table_div = driver.find_element(By.CSS_SELECTOR, 'div.trakMyAppTable')
    rows = table_div.find_elements(By.TAG_NAME, "tr")

    if not rows:
        message = "No application details found for the provided mobile number."
    else:
        message_lines = ["<b>Application Details:</b>"]
        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            if cols:
                line = " | ".join([col.text.strip() for col in cols])
                message_lines.append(line)
        message = "\n".join(message_lines)

    print(message)

    # Step 6: Send to Telegram
    if TELEGRAM_TOKEN and CHAT_ID:
        success = send_telegram_message(TELEGRAM_TOKEN, CHAT_ID, message)
        print("✅ Message sent to Telegram." if success else "❌ Failed to send Telegram message.")
    else:
        print("⚠️ Telegram credentials not found in environment variables.")

except Exception as e:
    print("❌ Error during scraping or sending message:", e)

finally:
    driver.quit()
