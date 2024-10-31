from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

# Configure Chrome options for headless mode
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Initialize the Chrome driver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# Open the page
url = "https://explorer.aptoslabs.com/validators/delegation?network=mainnet"
driver.get(url)

# Allow time for the page to load
time.sleep(5)

# Find all elements in the "Delegators" column
delegators_elements = driver.find_elements(By.XPATH, "//span[contains(@class, 'delegators')]")

# Extract numbers and sum them up
total_delegators = sum(int(element.text) for element in delegators_elements if element.text.isdigit())

# Print the total (you can also write it to a file or push it to a database)
print("Total Delegators:", total_delegators)

# Close the driver
driver.quit()
