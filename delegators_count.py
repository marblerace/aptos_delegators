import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

# Configure logging
logging.basicConfig(filename="debug.log", level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

logging.info("Starting script")

try:
    # Configure Chrome options for headless mode
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Initialize the Chrome driver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    logging.info("Chrome WebDriver initialized")

    # Open the page
    url = "https://explorer.aptoslabs.com/validators/delegation?network=mainnet"
    driver.get(url)
    logging.info(f"Opened URL: {url}")

    # Allow time for the page to load
    time.sleep(5)
    logging.info("Waited 5 seconds for page to load")

    # Find all elements in the "Delegators" column
    delegators_elements = driver.find_elements(By.XPATH, "//span[contains(@class, 'delegators')]")
    logging.info(f"Found {len(delegators_elements)} elements in the 'Delegators' column")

    # Check if any elements were found
    if not delegators_elements:
        logging.warning("No elements found in the 'Delegators' column. Check the XPath or page structure.")
    else:
        # Extract numbers and sum them up
        total_delegators = sum(int(element.text) for element in delegators_elements if element.text.isdigit())
        logging.info(f"Total delegators: {total_delegators}")

        # Write the result to README.md
        with open("README.md", "w") as file:
            file.write(f"# Delegators Count\n\nTotal Delegators: {total_delegators}\n")
        logging.info("Updated README.md with the total delegators count")

except Exception as e:
    logging.error("An error occurred", exc_info=True)
finally:
    # Close the driver
    driver.quit()
    logging.info("Closed the WebDriver")
