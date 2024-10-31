import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait  # Import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC  # Import EC for conditions
from webdriver_manager.chrome import ChromeDriverManager
import time

# Constants
op_usd_price = 1.368
total_op_drop = 19411313
total_op_usd_value = total_op_drop * op_usd_price

# Fetch APT price from CoinGecko
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
try:
    # Open the CoinGecko page for Aptos
    url = "https://www.coingecko.com/en/coins/aptos"
    driver.get(url)
    print(f"Opened URL: {url}")
    
    # Wait for the price element to load and retrieve the price text
    price_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//span[@data-converter-target='price']"))
    )
    apt_price_text = price_element.text.strip().replace("$", "")
    apt_price = float(apt_price_text)
    print(f"Current APT price fetched: ${apt_price}")
    
finally:
    driver.quit()
    print("Closed the WebDriver")

# Total amount in APT if Aptos spent the same as Optimism
d_value = total_op_usd_value / apt_price

# Load delegators data to find the last total delegators count
delegators_data = pd.read_csv("delegators_data.csv")
latest_total_delegators = delegators_data["Total Delegators"].iloc[-1]

# Calculate the amount per delegator
e_value = total_op_usd_value / latest_total_delegators
f_value = e_value / apt_price

# Update README.md with calculated values, adding line breaks for readability
with open("README.md", "a") as file:
    file.write(f"\n\nIf Aptos Foundation spent the same amount for the delegation airdrop as Optimism Foundation team (${total_op_usd_value:.2f}),\n")
    file.write(f"they will spend {d_value:.2f} APT for this airdrop.\n")
    file.write(f"With this logic, every APT delegate will receive on average: {f_value:.2f} APT (${e_value:.2f})\n")
