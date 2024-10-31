from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

print("Starting script")

try:
    # Configure Chrome options for headless mode
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    print("Chrome options configured for headless mode")

    # Initialize the Chrome driver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    print("Chrome WebDriver initialized")

    # Open the page
    url = "https://explorer.aptoslabs.com/validators/delegation?network=mainnet"
    driver.get(url)
    print(f"Opened URL: {url}")

    # Allow time for the page to load
    time.sleep(5)
    print("Waited 5 seconds for page to load")

    # Find all elements in the "Delegators" column
    delegators_elements = driver.find_elements(By.XPATH, "//span[contains(@class, 'delegators')]")
    print(f"Found {len(delegators_elements)} elements in the 'Delegators' column")

    # Check if any elements were found
    if not delegators_elements:
        print("Warning: No elements found in the 'Delegators' column. Check the XPath or page structure.")
    else:
        # Extract numbers and sum them up
        total_delegators = sum(int(element.text) for element in delegators_elements if element.text.isdigit())
        print(f"Total delegators: {total_delegators}")

        # Write the result to README.md
        with open("README.md", "w") as file:
            file.write(f"# Delegators Count\n\nTotal Delegators: {total_delegators}\n")
        print("Updated README.md with the total delegators count")

except Exception as e:
    print("An error occurred:", e)
finally:
    # Close the driver
    driver.quit()
    print("Closed the WebDriver")
