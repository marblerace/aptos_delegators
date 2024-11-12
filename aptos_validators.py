from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import re
from datetime import datetime, timezone, timedelta

# Initialize Chrome driver with options
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

url = "https://explorer.aptoslabs.com/validators/delegation?network=mainnet"
validators_file = "validators.txt"

# Ensure validators.txt is created if missing
open(validators_file, "w").close()

# Function to calculate precise unlock time
def calculate_unlock_time(remaining_time_str):
    days = hours = minutes = seconds = 0
    time_units = re.findall(r"(\d+)([dhms])", remaining_time_str)
    for amount, unit in time_units:
        if unit == 'd':
            days = int(amount)
        elif unit == 'h':
            hours = int(amount)
        elif unit == 'm':
            minutes = int(amount)
        elif unit == 's':
            seconds = int(amount)
    
    current_utc = datetime.now(timezone.utc)
    unlock_time = current_utc + timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
    return unlock_time.strftime("%d/%m/%Y %H:%M")

try:
    driver.get(url)
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, "//table//tbody")))
    print("Page loaded and table found.")

    # Scroll until all validator rows are loaded
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            print("Reached bottom of the page.")
            break
        last_height = new_height

    tbody = driver.find_element(By.XPATH, "//table//tbody")
    validator_rows = tbody.find_elements(By.XPATH, ".//a[@role='row']")
    print(f"Found {len(validator_rows)} validator rows in tbody.")

    # Write all validator URLs to a txt file
    with open(validators_file, "w") as file:
        for row in validator_rows:
            href = row.get_attribute("href")
            file.write(f"{href}\n")
    print(f"Saved {len(validator_rows)} URLs to {validators_file}")

    with open(validators_file, "r") as file:
        urls = file.readlines()

    # Process each validator link
    for i, url in enumerate(urls):
        url = url.strip()
        print(f"Opening validator {i + 1} URL: {url}")
        
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//p[contains(text(), 'Next Unlock')]")))

        next_unlock_element = driver.find_element(By.XPATH, "//p[text()='Next Unlock']")
        print(f"Found 'Next Unlock' <p> element for validator {i + 1}")

        span_elements = next_unlock_element.find_elements(By.XPATH, ".//following-sibling::span | .//ancestor::div//span")
        unlock_time_text = None

        for span in span_elements:
            if re.match(r"\d+d \d+h \d+m \d+s|\d+d \d+h \d+m|\d+h \d+m \d+s|\d+h \d+m", span.text):
                unlock_time_text = span.text
                break

        address = url.split("/validator/")[1].split("?")[0]
        if unlock_time_text:
            precise_unlock_time = calculate_unlock_time(unlock_time_text)
            print(f"Unlock time for validator {i + 1}: {precise_unlock_time}")
            urls[i] = f"{address}: {precise_unlock_time}\n"
        else:
            urls[i] = f"{address}: Unlock time not found\n"

        with open(validators_file, "w") as file:
            file.writelines(urls)

finally:
    driver.quit()
    print("Closed the WebDriver")
