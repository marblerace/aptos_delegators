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

    # Wait for the <table> element to load
    wait = WebDriverWait(driver, 30)
    table = wait.until(EC.presence_of_element_located((By.XPATH, "//table[@class='MuiTable-root css-81my7i']")))
    print("Located <table> element.")

    # Locate the <tbody> within the table
    tbody = table.find_element(By.XPATH, "./tbody[@class='MuiTableBody-root css-fzvvaf']")
    print("Located <tbody> within the table.")

    # Scroll to ensure dynamic content loads
    last_height = driver.execute_script("return document.body.scrollHeight")
    scroll_attempts = 0
    while scroll_attempts < 5:  # Scroll up to 5 times to load content
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)  # Wait to allow loading

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:  # Exit if no more content is loaded
            break
        last_height = new_height
        scroll_attempts += 1
    print("Scrolling complete, checking for rows...")

    # Find all <a> elements in the tbody which represent each validator row
    validator_rows = tbody.find_elements(By.XPATH, ".//a[@role='row']")
    print(f"Found {len(validator_rows)} validator rows after scrolling")

    # Initialize total for summing up the numbers
    total_delegators = 0

    # Loop through each row and retrieve the seventh <td> element
    for index, row in enumerate(validator_rows, start=1):
        print(f"\nProcessing row {index}")
        try:
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
