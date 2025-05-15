import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, WebDriverException
import requests

# === CONFIGURATION: Read from environment variables ===
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
        print("Telegram API Response:", response.text)
    return response.ok

def safe_click(driver, wait, locator):
    print(f"Waiting to click element: {locator}")
    element = wait.until(EC.element_to_be_clickable(locator))
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
    try:
        element.click()
        print(f"Clicked element: {locator}")
    except Exception as e:
        print(f"Standard click failed ({e}), attempting JS click")
        driver.execute_script("arguments[0].click();", element)
        print(f"JS Click successful: {locator}")
    return element

# === Setup Chrome WebDriver with headless mode and logging ===
options = Options()
options.add_argument("--headless=new")  # Headless mode
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument('--disable-gpu')
options.add_argument('--window-size=1920,1080')

# Set logging preferences via options
options.set_capability('goog:loggingPrefs', {'browser': 'ALL', 'driver': 'ALL'})

# Enable ChromeDriver logs to a file for debugging
service = Service(log_path="chromedriver.log")

print("Starting WebDriver...")
driver = webdriver.Chrome(service=service, options=options)
wait = WebDriverWait(driver, 15)

try:
    print("Navigating to the tracking page...")
    driver.get("https://swavlambancard.gov.in/track-your-application")

    print("Selecting 'Mobile Number' radio button...")
    safe_click(driver, wait, (By.ID, "cat-mobile"))

    print("Waiting for mobile number input box...")
    input_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[formcontrolname="mobile"]')))
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", input_box)
    input_box.clear()
    input_box.send_keys(MOBILE_NUMBER)
    print(f"Entered mobile number: {MOBILE_NUMBER}")

    print("Clicking Submit button...")
    safe_click(driver, wait, (By.CSS_SELECTOR, 'input[type="submit"][value="Submit"]'))

    print("Waiting for results table to appear...")
    table_div = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.trakMyAppTable')))
    print("Results table found, extracting data...")

    rows = table_div.find_elements(By.TAG_NAME, "tr")

    if not rows:
        message = "No application details found for the provided mobile number."
        print(message)
    else:
        message_lines = ["<b>Application Details:</b>"]
        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            if cols:
                line = " | ".join([col.text.strip() for col in cols])
                message_lines.append(line)
        message = "\n".join(message_lines)
        print("Application details extracted.")

    print("Sending message to Telegram...")
    success = send_telegram_message(TELEGRAM_TOKEN, CHAT_ID, message)
    if success:
        print("✅ Message sent to Telegram successfully.")
    else:
        print("❌ Failed to send message to Telegram.")

except TimeoutException as e:
    print(f"❌ Timeout error during wait: {e}")
except WebDriverException as e:
    print(f"❌ WebDriver error: {e}")
except Exception as e:
    print(f"❌ Unexpected error occurred: {e}")
finally:
    print("Closing WebDriver...")
    driver.quit()
    print("WebDriver closed.")
