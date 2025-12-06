import requests
from datetime import datetime

# Constants
COLLECTION_API_URL = "https://public-api.aptoscan.com/v1/accounts/{collection_id}/tokens"
EXPIRATION_API_URL = "https://www.aptosnames.com/api/v1/name/{domain}/expiration"
COLLECTION_ID = "0x63d26a4e3a8aeececf9b878e46bad78997fb38e50936efeabb2c4453f4d7f746"
OUTPUT_FILE = "valid_domains.txt"

def fetch_domains_from_collection(page=1):
    """Fetch domains from the Aptos .apt collection."""
    url = f"{COLLECTION_API_URL.replace('{collection_id}', COLLECTION_ID)}?page={page}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        print(f"Page {page} Response: {data}")  # Debug print
        return data.get("data", {}).get("list_trans", []), data.get("data", {}).get("count", 0)
    else:
        print(f"Error fetching collection data: {response.status_code} - {response.text}")
        return [], 0

def fetch_domain_expiration(domain_name):
    """Fetch the expiration timestamp of a domain using Aptos Names API."""
    url = EXPIRATION_API_URL.replace("{domain}", domain_name)
    response = requests.get(url)
    print(f"Fetching expiration for {domain_name}: {response.text}")  # Debug print
    if response.status_code == 200:
        expiration = response.json()
        if expiration:
            expiration_date = datetime.utcfromtimestamp(expiration / 1000)  # Convert ms to seconds
            return expiration_date
    return None

def get_valid_domains():
    """Fetch and filter valid (unexpired) domains from the collection."""
    valid_domains = []
    page = 1
    total_domains = 0

    with open(OUTPUT_FILE, "w") as file:
        while True:
            domains, total = fetch_domains_from_collection(page)
            if not domains:
                break

            total_domains += len(domains)
            print(f"Processing page {page} with {len(domains)} domains...")

            for domain in domains:
                domain_name = domain.get("name")
                if not domain_name:
                    continue

                expiration_date = fetch_domain_expiration(domain_name)

                if expiration_date and expiration_date > datetime.utcnow():
                    valid_domains.append({"name": domain_name, "expiration": expiration_date})
                    file.write(f"{domain_name}: {expiration_date.strftime('%Y-%m-%d %H:%M:%S')} UTC\n")

            # Check if there are more pages to process
            if len(domains) < total:
                break

            page += 1

        # Add summary at the end
        file.write("\n")
        file.write(f"Total domains: {total_domains}\n")
        file.write(f"Unexpired domains: {len(valid_domains)}\n")

    return valid_domains

# Main Script
if __name__ == "__main__":
    valid_domains = get_valid_domains()
    print("Domain processing complete. Results written to 'valid_domains.txt'.")
