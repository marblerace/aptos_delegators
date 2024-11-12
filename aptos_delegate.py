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
from datetime import datetime
import os

print("Starting script")

# Fetch current APT price from Aptos Scan API
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

# Retry mechanism for Selenium actions
def retry_action(driver, action, retries=3, wait_time=5):
    attempt = 0
    while attempt < retries:
        try:
            result = action()
            print(f"Attempt {attempt + 1} succeeded.")
            return result
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(wait_time)
            attempt += 1
    raise Exception(f"Failed to complete action after {retries} attempts.")

# Fetch the current APT price
apt_price = fetch_apt_price()

try:
    # Configure Selenium and scrape delegators and delegated amount
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    url = "https://explorer.aptoslabs.com/validators/delegation?network=mainnet"
    driver.get(url)
    print("Page loaded, waiting for table body element to be present.")

    # Retry locating the table body
    table_body = retry_action(driver, lambda: WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.XPATH, "//tbody[@class='MuiTableBody-root css-1013deo']"))
    ))
    print("Table body element located.")

    # Find tbody within the table
    tbody = table_body
    print("Tbody found:", "Yes" if tbody else "No")

    # Extract delegator rows within tbody using role attribute
    validator_rows = tbody.find_elements(By.XPATH, ".//a[@role='row']")
    print(f"Found {len(validator_rows)} validator rows in tbody.")

    # Scroll to load all rows
    last_height = driver.execute_script("return document.body.scrollHeight")
    for attempt in range(5):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            print("Reached bottom of the page.")
            break
        last_height = new_height

    total_delegators, total_apt_delegated = 0, 0
    for idx, row in enumerate(validator_rows, start=1):
        try:
            apt_delegated_td = row.find_elements(By.TAG_NAME, "td")[4]
            apt_delegated = int(apt_delegated_td.text.split(" ")[0].replace(",", ""))
            total_apt_delegated += apt_delegated
            print(f"Row {idx} - APT Delegated: {apt_delegated}")

            delegators_td = row.find_elements(By.TAG_NAME, "td")[6]
            delegators_count = int(delegators_td.text.replace(",", ""))
            total_delegators += delegators_count
            print(f"Row {idx} - Delegators Count: {delegators_count}")

        except (IndexError, ValueError) as e:
            print(f"Error processing row {idx} data:", e)

    # Check for zero total_delegators to avoid division by zero
    if total_delegators == 0:
        print("No delegators found, exiting to avoid division by zero.")
    else:
        print(f"Total Delegators: {total_delegators}")
        print(f"Total APT Delegated: {total_apt_delegated}")

    # Fetch the vesting data from CryptoRank
    driver.get("https://cryptorank.io/price/aptos/vesting")
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CLASS_NAME, "sc-5f77eb9d-0")))
    print("Navigated to CryptoRank vesting page.")

    # Scroll to ensure elements load fully
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 3);")
    time.sleep(2)  # Wait briefly for elements to load after scroll

    # Extract the total vesting amount
    vesting_amount_element = driver.find_element(By.XPATH, "//span[contains(@class, 'sc-56567222-0') and contains(@class, 'fzulHc')]")
    vesting_amount_text = vesting_amount_element.text if vesting_amount_element else ""
    print(f"Raw vesting amount text: {vesting_amount_text}")

    # Locate the unlock percentage from the table
    try:
        # Find the table body, then the third <tr> and its third <td>
        table_body = driver.find_element(By.XPATH, "//table[@class='sc-5f77eb9d-0 sc-b83f0aca-1 fKSPvD eeiGZr']/tbody")
        third_row = table_body.find_elements(By.TAG_NAME, "tr")[2]  # third <tr> (0-indexed)
        unlock_percentage_td = third_row.find_elements(By.TAG_NAME, "td")[2]  # third <td> (0-indexed)
        unlock_percentage_text = unlock_percentage_td.text if unlock_percentage_td else ""
    except Exception as e:
        unlock_percentage_text = ""
        print(f"Error finding unlock percentage in the table: {e}")

    print(f"Raw unlock percentage text: {unlock_percentage_text}")

    # Clean and convert vesting amount
    vesting_amount_text_cleaned = vesting_amount_text.replace("APT ", "")
    try:
        if "B" in vesting_amount_text_cleaned:
            vesting_amount = float(vesting_amount_text_cleaned.replace("B", "")) * 1_000_000_000
        elif "M" in vesting_amount_text_cleaned:
            vesting_amount = float(vesting_amount_text_cleaned.replace("M", "")) * 1_000_000
        else:
            vesting_amount = float(vesting_amount_text_cleaned)
        print(f"Converted vesting amount: {vesting_amount} APT")
    except ValueError as e:
        print("Error converting vesting amount:", e)
        vesting_amount = 0

    # Clean and convert unlock percentage
    try:
        unlock_percentage = float(unlock_percentage_text.replace("%", "")) / 100 if unlock_percentage_text else 0
        print(f"Converted unlock percentage: {unlock_percentage}")
    except ValueError as e:
        print("Error converting unlock percentage:", e)
        unlock_percentage = 0

    # Calculate unlocked APT and USD values
    unlocked_apt = vesting_amount * unlock_percentage
    unlocked_usd = unlocked_apt * apt_price
    print(f"Calculated unlocked APT: {unlocked_apt} APT")
    print(f"Calculated unlocked USD: ${unlocked_usd}")

    # Per delegator values
    g_value = unlocked_apt / total_delegators if total_delegators > 0 else 0
    h_value = unlocked_usd / total_delegators if total_delegators > 0 else 0
    print(f"Per delegator unlocked APT: {g_value}")
    print(f"Per delegator unlocked USD: ${h_value}")

    # Per delegator values
    g_value = unlocked_apt / total_delegators if total_delegators > 0 else 0
    h_value = unlocked_usd / total_delegators if total_delegators > 0 else 0
    print(f"Per delegator unlocked APT: {g_value}")
    print(f"Per delegator unlocked USD: ${h_value}")

    # Per delegator values
    g_value = unlocked_apt / total_delegators if total_delegators > 0 else 0
    h_value = unlocked_usd / total_delegators if total_delegators > 0 else 0
    print(f"Per delegator unlocked APT: {g_value}")
    print(f"Per delegator unlocked USD: ${h_value}")

    # Per delegator values
    g_value = unlocked_apt / total_delegators
    h_value = unlocked_usd / total_delegators

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