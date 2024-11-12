from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

# Configure Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
url = "https://explorer.aptoslabs.com/validators/delegation?network=mainnet"

try:
    driver.get(url)
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, "//tbody")))

    # Find validator rows by role attribute
    validator_rows = driver.find_elements(By.XPATH, "//tbody//a[@role='row']")
    print(f"Found {len(validator_rows)} validator rows.")

    # Iterate through each validator row
    for i, row in enumerate(validator_rows, start=1):
        row.click()  # Click to open the validator's detailed page
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//img[@alt='Identicon']")))

        # Select all Identicon elements and choose the second one
        identicon_elements = driver.find_elements(By.XPATH, "//img[@alt='Identicon']")
        if len(identicon_elements) >= 2:
            second_identicon = identicon_elements[1]
            print(f"Got for validator {i}")
        else:
            print(f"Validator {i}: Second Identicon not found")

        # Go back to the main page to click the next validator
        driver.back()
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//tbody")))

finally:
    driver.quit()
