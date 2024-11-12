import requests
import re
from datetime import datetime

validators_file = "validators.txt"
wallets_file = "wallets.txt"
results_file = "aptos_results.txt"

# Load validator unlock dates from validators.txt
def load_validators():
    validator_unlock_dates = {}
    try:
        with open(validators_file, "r") as file:
            for line in file:
                match = re.match(r"(0x[0-9a-fA-F]+): (\d{2}/\d{2}/\d{4} \d{2}:\d{2})", line.strip())
                if match:
                    validator_address = match.group(1)
                    unlock_date = datetime.strptime(match.group(2), "%d/%m/%Y %H:%M")
                    validator_unlock_dates[validator_address] = unlock_date
    except FileNotFoundError:
        print(f"{validators_file} not found. Please ensure this file exists.")
    return validator_unlock_dates

def fetch_transactions(wallet_address):
    url = f"https://public-api.aptoscan.com/v1/accounts/{wallet_address}/coin-transfers"
    headers = {
        "accept": "application/json",
        "User-Agent": "Mozilla/5.0"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        transactions_data = response.json()

        if transactions_data.get("success") and "data" in transactions_data:
            return transactions_data["data"].get("list_trans", [])
        else:
            print("Unexpected structure of transactions:", transactions_data)
            return None

    except requests.exceptions.HTTPError as e:
        print(f"HTTP error occurred: {e}")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching transactions: {e}")

# Process each wallet to check for delegations to validators
def process_wallets():
    validator_unlock_dates = load_validators()
    delegation_groups = {}

    try:
        with open(wallets_file, "r") as wallet_file:
            for line_index, wallet in enumerate(wallet_file, start=1):
                wallet = wallet.strip()
                print(f"Processing wallet {line_index}: {wallet}")
                transactions = fetch_transactions(wallet)
                
                if transactions is None:
                    print(f"No transactions found for wallet {wallet}")
                    continue

                found_validator = False
                for transaction in transactions:
                    send_to = transaction.get("send_to")
                    if send_to in validator_unlock_dates:
                        unlock_date = validator_unlock_dates[send_to]
                        print(f"Found delegation transaction to validator {send_to} for wallet {wallet}")

                        if (send_to, unlock_date) not in delegation_groups:
                            delegation_groups[(send_to, unlock_date)] = []
                        delegation_groups[(send_to, unlock_date)].append((line_index, wallet))

                        found_validator = True
                        break

                if not found_validator:
                    print(f"No matching validator transaction found for wallet {wallet}")
                    
        # Sort the groups by the earliest unlock date
        sorted_delegations = sorted(delegation_groups.items(), key=lambda x: x[0][1])

        # Write results to aptos_results.txt in the specified format
        with open(results_file, "w") as result_file:
            for (validator, unlock_date), wallets in sorted_delegations:
                formatted_date = unlock_date.strftime("%d/%m/%Y %H:%M")
                result_file.write(f"Delegated to {validator}. Unlock on: {formatted_date}\n")
                
                for line_index, wallet in wallets:
                    result_file.write(f"({line_index}) {wallet}\n")
                
                result_file.write("\n\n\n")

    except FileNotFoundError:
        print(f"{wallets_file} not found. Please ensure this file exists.")

process_wallets()
