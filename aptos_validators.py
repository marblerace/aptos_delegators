from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
url = "https://explorer.aptoslabs.com/validators/delegation?network=mainnet"

try:
    driver.get(url)
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, "//tbody")))

    # Find validator rows by role attribute and get their href
    validator_rows = driver.find_elements(By.XPATH, "//tbody//a[@role='row']")
    print(f"Found {len(validator_rows)} validator rows.")

    # Iterate through each validator row
    for i, row in enumerate(validator_rows, start=1):
        href = row.get_attribute("href")  # Get the relative href
        full_url = f"https://explorer.aptoslabs.com{href}"
        
        # Open the validator's detailed page
        driver.get(full_url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//img[@alt='Identicon']")))

        # Select all Identicon elements and choose the second one
        identicon_elements = driver.find_elements(By.XPATH, "//img[@alt='Identicon']")
        if len(identicon_elements) >= 2:
            print(f"Got Identicon for validator {i}")
        else:
            print(f"Validator {i}: Second Identicon not found")

        # Return to the main page
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//tbody")))

finally:
    driver.quit()