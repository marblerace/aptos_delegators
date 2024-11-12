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
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//img[@alt='Identicon']")))

        # Locate Identicon images and confirm if the second one is found
        identicon_elements = driver.find_elements(By.XPATH, "//img[@alt='Identicon']")
        if len(identicon_elements) >= 2:
            print(f"Got Identicon for validator {i + 1}")

        # Update validators.txt to replace the URL with got[i]
        urls[i] = f"got[{i}]\n"
        with open(validators_file, "w") as file:
            file.writelines(urls)

finally:
    driver.quit()
    print("Closed the WebDriver")
