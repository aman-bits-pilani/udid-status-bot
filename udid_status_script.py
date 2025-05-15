from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import os
import requests

# === CONFIGURATION ===
MOBILE_NUMBER = os.getenv("MOBILE_NUMBER")  # Replace with your actual mobile number
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
    return response.ok

# === Setup Chrome WebDriver ===
options = Options()
options.add_argument('--start-maximized')
driver = webdriver.Chrome(options=options)

try:
    # Step 1: Open the website
    driver.get("https://swavlambancard.gov.in/track-your-application")
    time.sleep(2)

    # Step 2: Select the "Mobile Number" radio option
    driver.find_element(By.ID, "cat-mobile").click()
    time.sleep(1)

    # Step 3: Enter the mobile number
    input_box = driver.find_element(By.CSS_SELECTOR, 'input[formcontrolname="mobile"]')
    input_box.send_keys(MOBILE_NUMBER)

    # Step 4: Click the Submit button
    submit_btn = driver.find_element(By.CSS_SELECTOR, 'input[type="submit"][value="Submit"]')
    submit_btn.click()

    # Step 5: Wait for the result table to appear
    time.sleep(3)

    # Step 6: Extract table content
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

    # Print to console
    print(message)

    # Step 7: Send to Telegram
    success = send_telegram_message(TELEGRAM_TOKEN, CHAT_ID, message)
    if success:
        print("✅ Message sent to Telegram successfully.")
    else:
        print("❌ Failed to send message to Telegram.")

except Exception as e:
    print("❌ Error during scraping or sending message:", e)

finally:
    # Step 8: Close browser
    driver.quit()
