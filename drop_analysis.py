import pandas as pd
import requests

# Constants
op_usd_price = 1.368
total_op_drop = 19411313
total_op_usd_value = total_op_drop * op_usd_price

# Fetch APT price from Aptos Scan API
url = "https://public-api.aptoscan.com/v1/coins/0x1%3A%3Aaptos_coin%3A%3AAptosCoin"
response = requests.get(url)
data = response.json()

# Extract current APT price
if response.status_code == 200 and data["success"]:
    apt_price = data["data"]["current_price"]
    print(f"Current APT price fetched: ${apt_price}")
else:
    raise ValueError("Failed to fetch APT price from Aptos Scan API")

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
