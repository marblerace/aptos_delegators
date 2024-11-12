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

try:
    driver.get(url)
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, "//table//tbody")))
    print("Page loaded and table found.")

    # Scroll until all validator rows are loaded
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)  # Give time for new rows to load
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            print("Reached bottom of the page.")
            break
        last_height = new_height

    # Locate tbody and find all validator row elements with href attribute
    tbody = driver.find_element(By.XPATH, "//table//tbody")
    validator_rows = tbody.find_elements(By.XPATH, ".//a[@role='row']")
    print(f"Found {len(validator_rows)} validator rows in tbody.")

    # Step 1: Write all validator URLs to a txt file
    with open(validators_file, "w") as file:
        for row in validator_rows:
            href = row.get_attribute("href")
            file.write(f"{href}\n")
    print(f"Saved {len(validator_rows)} URLs to {validators_file}")

    # Step 2: Read URLs from txt file, process each, and update file with got[i] marks
    with open(validators_file, "r") as file:
        urls = file.readlines()

    # Process each validator link from the file
    for i, url in enumerate(urls):
        url = url.strip()
        print(f"Opening validator {i + 1} URL: {url}")
        
        # Open each validator link
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//p[contains(text(), 'Next Unlock')]")))

        # Locate the <p> element with text "Next Unlock"
        next_unlock_element = driver.find_element(By.XPATH, "//p[text()='Next Unlock']")
        print(f"Found 'Next Unlock' <p> element for validator {i + 1}")

        # Retrieve all <span> elements within the same parent or sibling hierarchy
        span_elements = next_unlock_element.find_elements(By.XPATH, ".//following-sibling::span | .//ancestor::div//span")
        unlock_time = None

        for span in span_elements:
            # Check if the span text contains a pattern for time like '9d 11h 54m 15s'
            if re.match(r"\d+d \d+h \d+m \d+s|\d+d \d+h \d+m|\d+h \d+m \d+s|\d+h \d+m", span.text):
                unlock_time = span.text
                break  # Stop once the time string is found

        # Extract the validator address from the URL
        address = url.split("/validator/")[1].split("?")[0]
        print(f"Validator {i + 1} address: {address}")
        print(f"Unlock time for validator {i + 1}: {unlock_time}")

        # Update validators.txt with the address and unlock time
        if unlock_time:
            urls[i] = f"{address}: {unlock_time}\n"
        else:
            urls[i] = f"{address}: Unlock time not found\n"  # In case unlock time is missing

        with open(validators_file, "w") as file:
            file.writelines(urls)





    def calculate_unlock_time(remaining_time_str):
        """Calculate the precise unlock time given a remaining time string."""
        # Parse the remaining time string
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
        
        # Add parsed time to the current UTC time
        current_utc = datetime.now(timezone.utc)
        unlock_time = current_utc + timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
        
        # Format the unlock time as DD/MM/YYYY HH:MM
        return unlock_time.strftime("%d/%m/%Y %H:%M")

    # Process each validator link from the file
    for i, url in enumerate(urls):
        url = url.strip()
        print(f"Opening validator {i + 1} URL: {url}")
        
        # Open each validator link
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//p[contains(text(), 'Next Unlock')]")))

        # Locate the <p> element with text "Next Unlock"
        next_unlock_element = driver.find_element(By.XPATH, "//p[text()='Next Unlock']")
        print(f"Found 'Next Unlock' <p> element for validator {i + 1}")

        # Retrieve all <span> elements within the same parent or sibling hierarchy
        span_elements = next_unlock_element.find_elements(By.XPATH, ".//following-sibling::span | .//ancestor::div//span")
        unlock_time_text = None

        for span in span_elements:
            # Check if the span text contains a pattern for time like '9d 11h 54m 15s'
            if re.match(r"\d+d \d+h \d+m \d+s|\d+d \d+h \d+m|\d+h \d+m \d+s|\d+h \d+m", span.text):
                unlock_time_text = span.text
                break  # Stop once the time string is found

        # Extract the validator address from the URL
        address = url.split


finally:
    driver.quit()
    print("Closed the WebDriver")
