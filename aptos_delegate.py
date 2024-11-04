from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import requests
import pandas as pd
import matplotlib.pyplot as plt
import time
import os
from datetime import datetime

print("Starting script")

# 1. Fetch current APT price from Aptos Scan API
def fetch_apt_price():
    url = "https://public-api.aptoscan.com/v1/coins/0x1%3A%3Aaptos_coin%3A%3AAptosCoin"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        if data.get("success"):
            apt_price = data["data"]["current_price"]
            print(f"Current APT price fetched: ${apt_price}")
            return apt_price
        else:
            raise ValueError("Failed to fetch APT price: API response indicates failure")
    except requests.RequestException as e:
        print("Error fetching data from Aptos Scan API:", e)
        return 0.0

# Fetch the current APT price
apt_price = fetch_apt_price()

try:
    # 2. Configure Selenium and scrape delegators and delegated amount
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    url = "https://explorer.aptoslabs.com/validators/delegation?network=mainnet"
    driver.get(url)
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, "//tbody[@class='MuiTableBody-root css-fzvvaf']")))

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
    validator_rows = driver.find_elements(By.XPATH, "//tbody[@class='MuiTableBody-root css-fzvvaf']//a[@role='row']")
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
    driver.get("https://cryptorank.io/price/aptos/vesting")
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CLASS_NAME, "sc-56567222-0")))

    # Extract the total vesting amount and unlock percentage
    vesting_amount_text = driver.find_element(By.XPATH, "//span[contains(@class, 'sc-56567222-0') and contains(@class, 'fzulHc')]").text
    unlock_percentage_text = driver.find_element(By.XPATH, "//span[contains(@class, 'sc-56567222-0') and contains(@class, 'ftrvre')]").text

    # Clean and convert vesting amount
    vesting_amount_text = vesting_amount_text.replace("APT ", "").replace("B", "").replace("M", "")
    try:
        if "B" in vesting_amount_text:
            vesting_amount = float(vesting_amount_text) * 1_000_000_000
        elif "M" in vesting_amount_text:
            vesting_amount = float(vesting_amount_text) * 1_000_000
        else:
            vesting_amount = float(vesting_amount_text)
    except ValueError as e:
        print("Error converting vesting amount:", e)
        vesting_amount = 0  # Fallback in case of error

    # Clean and convert unlock percentage
    try:
        unlock_percentage = float(unlock_percentage_text.replace("%", "")) / 100
    except ValueError as e:
        print("Error converting unlock percentage:", e)
        unlock_percentage = 0  # Fallback in case of error

    unlocked_apt = vesting_amount * unlock_percentage
    unlocked_usd = unlocked_apt * apt_price

    # Per delegator values
    g_value = unlocked_apt / total_delegators
    h_value = unlocked_usd / total_delegators

    # Append data to CSV and generate plot
    data = pd.DataFrame([[datetime.now(), total_delegators, total_apt_delegated]], columns=["Date", "Total Delegators", "Total APT Delegated"])
    if os.path.exists("delegators_data.csv"):
        data.to_csv("delegators_data.csv", mode='a', header=False, index=False)
    else:
        data.to_csv("delegators_data.csv", index=False)

    # Read data and plot
    if os.path.exists("delegators_data.csv"):
        data = pd.read_csv("delegators_data.csv")
    plt.figure(figsize=(10, 6))
    plt.plot(data["Total Delegators"], color="white", linewidth=2)
    plt.gca().axis("off")  # Turn off axes
    plt.gca().set_facecolor("#2E2E2E")
    plt.gcf().set_facecolor("#2E2E2E")
    plt.savefig("delegators.png", facecolor="#2E2E2E")
    plt.close()

    # 4. Analyze OP airdrop data
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
        file.write(f"![Delegators Plot](delegators.png)<br><br>\n")
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