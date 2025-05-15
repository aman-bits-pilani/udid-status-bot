from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
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
    if not response.ok:
        print("Telegram API Response:", response.text)
    return response.ok

def safe_click(driver, wait, locator):
    element = wait.until(EC.element_to_be_clickable(locator))
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
    try:
        element.click()
    except Exception:
        driver.execute_script("arguments[0].click();", element)
    return element

# === Setup Chrome WebDriver ===
options = Options()
options.add_argument('--start-maximized')
# options.add_argument('--headless')  # Avoid headless if interaction issues
options.add_argument("--disable-gpu")

driver = webdriver.Chrome(options=options)

try:
    wait = WebDriverWait(driver, 15)
    driver.get("https://swavlambancard.gov.in/track-your-application")

    # Simulate small mouse movement and scroll to keep page active
    actions = ActionChains(driver)
    actions.move_by_offset(1, 1).perform()
    actions.move_by_offset(-1, -1).perform()
    driver.execute_script("window.scrollBy(0, 1);")
    driver.execute_script("window.scrollBy(0, -1);")

    # Step 2: Select the "Mobile Number" radio option
    safe_click(driver, wait, (By.ID, "cat-mobile"))

    # Step 3: Enter the mobile number
    input_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[formcontrolname="mobile"]')))
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", input_box)
    input_box.clear()
    input_box.send_keys(MOBILE_NUMBER)

    # Step 4: Click the Submit button
    safe_click(driver, wait, (By.CSS_SELECTOR, 'input[type="submit"][value="Submit"]'))

    # Step 5: Wait for the result table to appear
    table_div = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.trakMyAppTable')))
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
    success = send_telegram_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, message)
    if success:
        print("✅ Message sent to Telegram successfully.")
    else:
        print("❌ Failed to send message to Telegram.")

except Exception as e:
    print("❌ Error during scraping or sending message:", e)

finally:
    driver.quit()
