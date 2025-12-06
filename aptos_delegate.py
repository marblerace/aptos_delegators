from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
import requests
import pandas as pd
import matplotlib.pyplot as plt
import time
import os
from datetime import datetime

print("Starting script")

def fetch_apt_price():
    """Fetch current APT price using resilient fallbacks."""
    headers = {"User-Agent": "Mozilla/5.0"}

    # Primary: CoinGecko
    try:
        response = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": "aptos", "vs_currencies": "usd"},
            headers=headers,
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        price = data.get("aptos", {}).get("usd")
        if price:
            print(f"Current APT price fetched from CoinGecko: ${price}")
            return float(price)
    except requests.RequestException as e:
        print("CoinGecko price fetch failed:", e)

    # Fallback: Coinbase
    try:
        response = requests.get(
            "https://api.coinbase.com/v2/prices/APT-USD/spot",
            headers=headers,
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        amount = data.get("data", {}).get("amount")
        if amount:
            price = float(amount)
            print(f"Current APT price fetched from Coinbase: ${price}")
            return price
    except requests.RequestException as e:
        print("Coinbase price fetch failed:", e)

    # Last resort
    print("Falling back to APT price = 0 due to fetch failures.")
    return 0.0

# Fetch the current APT price
apt_price = fetch_apt_price()
if apt_price <= 0:
    # Avoid division by zero; still allow script to continue so README updates
    apt_price = 1.0
    print("Using fallback APT price of $1.0 to avoid division errors.")

try:
    # Configure Selenium and scrape delegators and delegated amount
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    url = "https://explorer.aptoslabs.com/validators/delegation?network=mainnet"
    driver.set_page_load_timeout(45)
    driver.get(url)
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, "//table//tbody")))

    # Scroll to load all rows
    last_height = driver.execute_script("return document.body.scrollHeight")
    for _ in range(5):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    # Extract delegators and delegated data
    #validator_rows = driver.find_elements(By.XPATH, "//tbody[@class='MuiTableBody-root css-1013deo']//a[@role='row']")
    tbody = driver.find_element(By.XPATH, "//table//tbody")
    validator_rows = tbody.find_elements(By.XPATH, ".//a[@role='row']")
    print(f"Found {len(validator_rows)} validator rows in tbody.")

    total_delegators, total_apt_delegated = 0, 0
    for row in validator_rows:
        try:
            apt_delegated_td = row.find_elements(By.TAG_NAME, "td")[4]
            total_apt_delegated += int(apt_delegated_td.text.split(" ")[0].replace(",", ""))
            delegators_td = row.find_elements(By.TAG_NAME, "td")[6]
            total_delegators += int(delegators_td.text.replace(",", ""))
        except (IndexError, ValueError) as e:
            print("Error processing row data:", e)

    # Fetch the vesting data from CryptoRank
    # Safely pull vesting data from CryptoRank
    vesting_amount = 0
    unlock_percentage = 0
    try:
        driver.get("https://cryptorank.io/price/aptos/vesting")
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        print("Navigated to CryptoRank vesting page.")

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 3);")
        time.sleep(2)

        # More tolerant selectors: pick first big number containing APT and first percent in the table
        vesting_amount_element = driver.find_element(By.XPATH, "//span[contains(text(),'APT')]")
        vesting_amount_text = vesting_amount_element.text if vesting_amount_element else ""
        print(f"Raw vesting amount text: {vesting_amount_text}")

        unlock_percentage_element = driver.find_element(By.XPATH, "//table/tbody/tr[3]/td[3]")
        unlock_percentage_text = unlock_percentage_element.text if unlock_percentage_element else ""
        print(f"Raw unlock percentage text: {unlock_percentage_text}")

        vesting_amount_text_cleaned = vesting_amount_text.replace("APT ", "").replace(",", "")
        if "B" in vesting_amount_text_cleaned:
            vesting_amount = float(vesting_amount_text_cleaned.replace("B", "")) * 1_000_000_000
        elif "M" in vesting_amount_text_cleaned:
            vesting_amount = float(vesting_amount_text_cleaned.replace("M", "")) * 1_000_000
        else:
            vesting_amount = float(vesting_amount_text_cleaned)

        unlock_percentage = float(unlock_percentage_text.replace("%", "").replace(",", "")) / 100 if unlock_percentage_text else 0
        print(f"Converted vesting amount: {vesting_amount} APT")
        print(f"Converted unlock percentage: {unlock_percentage}")
    except (TimeoutException, NoSuchElementException, ValueError, WebDriverException) as e:
        print(f"Vesting data fetch failed, defaulting to 0: {e}")
        vesting_amount = 0
        unlock_percentage = 0

    unlocked_apt = vesting_amount * unlock_percentage
    unlocked_usd = unlocked_apt * apt_price
    print(f"Calculated unlocked APT: {unlocked_apt} APT")
    print(f"Calculated unlocked USD: ${unlocked_usd}")

    g_value = unlocked_apt / total_delegators if total_delegators > 0 else 0
    h_value = unlocked_usd / total_delegators if total_delegators > 0 else 0
    print(f"Per delegator unlocked APT: {g_value}")
    print(f"Per delegator unlocked USD: ${h_value}")

    # Prepare data for CSV as a list of lists
    data_row = [[datetime.now(), total_delegators, total_apt_delegated]]

    # Check if the file exists to determine write mode
    if os.path.exists("delegators_data.csv"):
        # Append row as CSV-formatted text, ensuring a newline for each row
        with open("delegators_data.csv", mode='a') as file:
            pd.DataFrame(data_row, columns=["Date", "Total Delegators", "Total APT Delegated"]).to_csv(file, header=False, index=False)
    else:
        # Write header only if file is new
        pd.DataFrame(data_row, columns=["Date", "Total Delegators", "Total APT Delegated"]).to_csv("delegators_data.csv", index=False)

    # Read data from CSV
    if os.path.exists("delegators_data.csv"):
        data = pd.read_csv("delegators_data.csv")

    # Determine y-axis range and intervals
    min_delegators = int(data["Total Delegators"].min() // 500 * 500)  # Round down to nearest 500
    max_delegators = int(data["Total Delegators"].max() // 500 * 500 + 500)  # Round up to nearest 500
    y_ticks = list(range(min_delegators, max_delegators + 1, 500))

    # Create the plot
    plt.figure(figsize=(10, 6))
    plt.plot(data["Total Delegators"], color="white", linewidth=2)

    # Add y-axis labels for every 500 increments
    plt.yticks(y_ticks, color="white")
    plt.gca().set_facecolor("#2E2E2E")
    plt.gcf().set_facecolor("#2E2E2E")
    plt.gca().xaxis.set_visible(False)  # Hide the x-axis

    # Save the plot
    plt.savefig("delegators_plot.png", facecolor="#2E2E2E")
    plt.close()

    # Analyze OP airdrop data
    op_data = pd.read_csv("op_airdrop_3_simple_list.csv")
    op_usd_price = 1.368
    total_op_drop = 19411313
    average_op = op_data["total_op"].mean()
    median_op = op_data["total_op"].median()
    total_op_usd_value = total_op_drop * op_usd_price

    # Calculate hypothetical APT drop values
    d_value = total_op_usd_value / apt_price
    e_value = total_op_usd_value / total_delegators
    f_value = e_value / apt_price

    # Write all results to README.md with line breaks for readability and plot reference
    with open("README.md", "w") as file:
        file.write(f"# Delegators Count (APT ${apt_price:.2f})<br><br>\n")
        file.write(f"Total Delegators: {total_delegators}<br>\n")
        file.write(f"Total APT Delegated: {total_apt_delegated}<br><br>\n")
        file.write(f"![Delegators Plot](delegators_plot.png)<br><br>\n")
        file.write(f"**OP received for the third airdrop on 18.09.2023 (price of OP was ${op_usd_price}):**<br>\n")
        file.write(f"Addresses received drop: {len(op_data)}<br>\n")
        file.write(f"Average amount received: {average_op:.2f} (${average_op * op_usd_price:.2f})<br>\n")
        file.write(f"Median amount received: {median_op:.2f} (${median_op * op_usd_price:.2f})<br>\n")
        file.write(f"Total drop distribution: {total_op_drop} (${total_op_usd_value:.2f})<br><br>\n")
        file.write(f"If Aptos Foundation team spent the same amount for the delegation airdrop as Optimism Foundation team (${total_op_usd_value:.2f}),<br>\n")
        file.write(f"they will spend {d_value:.2f} APT for this airdrop.<br>\n")
        file.write(f"With this logic, every APT delegate will receive on average: {f_value:.2f} APT (${e_value:.2f})<br><br>\n")
        file.write(f"Currently Foundation team has unlocked: {unlocked_apt:.2f} APT (${unlocked_usd:.2f})<br>\n")
        file.write(f"If Aptos Foundation team spent this amount for the delegation airdrop, every APT delegate will receive : {g_value:.2f} APT (${h_value:.2f})<br>\n")

except Exception as e:
    print("An error occurred:", e)
finally:
    driver.quit()
    print("Closed the WebDriver")
