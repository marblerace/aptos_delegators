from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

# Initialize Chrome driver with options
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

url = "https://explorer.aptoslabs.com/validators/delegation?network=mainnet"

try:
    driver.get(url)
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, "//table//tbody")))
    print("Page loaded and table found.")

    # Locate tbody and find all validator row elements with href attribute
    tbody = driver.find_element(By.XPATH, "//table//tbody")
    validator_rows = tbody.find_elements(By.XPATH, ".//a[@role='row']")
    print(f"Found {len(validator_rows)} validator rows in tbody.")

    # Loop through each validator row to get href link and open it
    for i, row in enumerate(validator_rows, start=1):
        href = row.get_attribute("href")
        full_url = f"https://explorer.aptoslabs.com{href}"
        print(f"Opening validator {i} URL: {full_url}")
        
        # Open each validator link
        driver.get(full_url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//img[@alt='Identicon']")))

        # Locate Identicon images and print if the second one is found
        identicon_elements = driver.find_elements(By.XPATH, "//img[@alt='Identicon']")
        if len(identicon_elements) >= 2:
            print(f"Got Identicon for validator {i}")
        else:
            print(f"Validator {i}: Second Identicon not found")

        # Return to the main page for the next validator
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//table//tbody")))

finally:
    driver.quit()
    print("Closed the WebDriver")
