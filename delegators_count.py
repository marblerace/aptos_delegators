from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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

    # Allow time for the page to load fully and print the page source
    wait = WebDriverWait(driver, 15)
    wait.until(EC.presence_of_all_elements_located((By.XPATH, "//tbody[@class='MuiTableBody-root css-fzvvaf']")))
    print("Table body located")

    # Print the entire page source to check if elements are loaded
    print("Page source after load:\n", driver.page_source)

    # Locate the table body to ensure it’s found
    table_body = driver.find_element(By.XPATH, "//tbody[@class='MuiTableBody-root css-fzvvaf']")
    print("Located <tbody> element:\n", table_body.get_attribute("outerHTML"))

    # Find all <a> elements in the tbody which represent each validator row
    validator_rows = driver.find_elements(By.XPATH, "//tbody[@class='MuiTableBody-root css-fzvvaf']//a[@role='row']")
    print(f"Found {len(validator_rows)} validator rows")

    # Initialize total for summing up the numbers
    total_delegators = 0

    # Loop through each row and retrieve the seventh <td> element
    for index, row in enumerate(validator_rows, start=1):
        print(f"\nProcessing row {index}")
        try:
            # Print the outer HTML of the <a> row to verify structure
            print(f"HTML content of row {index}:\n", row.get_attribute("outerHTML"))

            # Get the seventh <td> within this row
            delegators_td = row.find_elements(By.XPATH, "./td[@class='MuiTableCell-root MuiTableCell-body MuiTableCell-sizeMedium css-x79huy']")[6]
            number = int(delegators_td.text)
            total_delegators += number
            print(f"Found delegators count in row {index}: {number}")
        except (IndexError, ValueError) as e:
            print(f"Could not retrieve or convert number in row {index}: {e}")

    print(f"\nTotal delegators: {total_delegators}")

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
