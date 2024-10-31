import matplotlib.pyplot as plt
import pandas as pd
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

# Helper function to plot the data
def plot_total_delegators():
    # Load existing data from CSV
    if os.path.exists("delegators_data.csv"):
        data = pd.read_csv("delegators_data.csv")
    else:
        data = pd.DataFrame(columns=["Date", "Total Delegators"])

    # Plotting
    plt.figure(figsize=(10, 6))
    plt.plot(data["Total Delegators"], color="white", linewidth=2)
    plt.title("Aptos Delegators Over Time", color="white")
    plt.ylabel("Total Delegators (in Thousands)", color="white")
    plt.grid(True, color="gray", linestyle="--", linewidth=0.5)
    plt.xticks([])
    plt.yticks([45000, 46000, 47000], color="white")
    plt.gca().set_facecolor("#2E2E2E")
    plt.gcf().set_facecolor("#2E2E2E")

    # Save the plot
    plt.savefig("delegators_plot.png", facecolor="#2E2E2E")
    plt.close()

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

    # Wait until table body is loaded
    wait = WebDriverWait(driver, 30)
    wait.until(EC.presence_of_element_located((By.XPATH, "//tbody[@class='MuiTableBody-root css-fzvvaf']")))
    print("Table body located")

    # Scroll to ensure dynamic content loads
    last_height = driver.execute_script("return document.body.scrollHeight")
    scroll_attempts = 0
    while scroll_attempts < 5:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
        scroll_attempts += 1
    print("Scrolling complete, checking for rows...")

    # Find all <a> elements in the tbody which represent each validator row
    validator_rows = driver.find_elements(By.XPATH, "//tbody[@class='MuiTableBody-root css-fzvvaf']//a[@role='row']")
    print(f"Found {len(validator_rows)} validator rows after scrolling")

    # Initialize totals for summing up the numbers
    total_delegators = 0
    total_apt_delegated = 0

    # Loop through each row and retrieve the values by index
    for index, row in enumerate(validator_rows, start=1):
        print(f"\nProcessing row {index}")
        try:
            # Get the total APT delegated (two indices before delegators)
            apt_delegated_td = row.find_elements(By.TAG_NAME, "td")[4]
            apt_delegated_text = apt_delegated_td.text.split(" ")[0].replace(",", "")
            apt_delegated = int(apt_delegated_text)
            total_apt_delegated += apt_delegated
            print(f"Found APT delegated in row {index}: {apt_delegated}")

            # Get the delegators count (seventh <td>)
            delegators_td = row.find_elements(By.TAG_NAME, "td")[6]
            delegators_count = int(delegators_td.text.replace(",", ""))
            total_delegators += delegators_count
            print(f"Found delegators count in row {index}: {delegators_count}")
        except (IndexError, ValueError) as e:
            print(f"Could not retrieve or convert data in row {index}: {e}")

    # Write the result to README.md
    with open("README.md", "w") as file:
        file.write(f"# Delegators Count\n\nTotal Delegators: {total_delegators}\n\nTotal APT Delegated: {total_apt_delegated}\n")
    print("Updated README.md with the total delegators count and APT delegated")

    # Save data to CSV for plotting
    data = pd.DataFrame([[datetime.now(), total_delegators]], columns=["Date", "Total Delegators"])
    if os.path.exists("delegators_data.csv"):
        data.to_csv("delegators_data.csv", mode='a', header=False, index=False)
    else:
        data.to_csv("delegators_data.csv", index=False)

    # Generate the plot
    plot_total_delegators()
    print("Plot updated successfully.")

except Exception as e:
    print("An error occurred:", e)
finally:
    # Close the driver
    driver.quit()
    print("Closed the WebDriver")
