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

    # Scroll to load all rows
    last_height = driver.execute_script("return document.body.scrollHeight")
    for _ in range(5):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    # Initialize a loop to find validator rows and navigate to their pages
    num_validators = 40  # Replace with actual count if needed
    for i in range(num_validators):
        # Re-fetch the validator rows on each iteration to avoid stale element issues
        tbody = driver.find_element(By.XPATH, "//table//tbody")
        validator_rows = tbody.find_elements(By.XPATH, ".//a[@role='row']")
        
        if i >= len(validator_rows):
            print(f"Validator {i + 1} could not be found, ending iteration.")
            break

        # Get href and navigate to the validator's detailed page
        href = validator_rows[i].get_attribute("href")
        print(f"Opening validator {i + 1} URL: {href}")
        driver.get(href)
        
        # Wait for the Identicon to load on the validator's detail page
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//img[@alt='Identicon']")))
        identicon_elements = driver.find_elements(By.XPATH, "//img[@alt='Identicon']")
        
        if len(identicon_elements) >= 2:
            print(f"Got Identicon for validator {i + 1}")
        else:
            print(f"Validator {i + 1}: Second Identicon not found")

        # Navigate back to the main page
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//table//tbody")))

finally:
    driver.quit()
    print("Closed the WebDriver")
