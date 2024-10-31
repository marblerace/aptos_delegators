import matplotlib.pyplot as plt
import pandas as pd

# Load historical delegators data
data = pd.read_csv("delegators_data.csv")

# Plot Total Delegators Over Time
plt.figure(figsize=(10, 6))
plt.plot(data["Total Delegators"], color="white", linewidth=2)
plt.title("Aptos Delegators Over Time", color="white")
plt.ylabel("Total Delegators (in Thousands)", color="white")
plt.grid(True, color="gray", linestyle="--", linewidth=0.5)
plt.xticks([])
plt.yticks([45000, 46000, 47000], color="white")
plt.gca().set_facecolor("#2E2E2E")
plt.gcf().set_facecolor("#2E2E2E")
plt.savefig("delegators_plot.png", facecolor="#2E2E2E")
plt.close()

# Load OP airdrop data
op_data = pd.read_csv("op_airdrop_3_simple_list.csv")
total_op_drop = 19411313
op_usd_price = 1.368

# Calculate average and median amounts, then convert to USD
average_op = op_data["total_op"].mean()
median_op = op_data["total_op"].median()
average_op_usd = average_op * op_usd_price
median_op_usd = median_op * op_usd_price
total_drop_usd = total_op_drop * op_usd_price

# Update README.md with additional information
with open("README.md", "a") as file:
    file.write(f"\nOP received for the third airdrop on 18.09.2023 (price of OP was ${op_usd_price}):\n")
    file.write(f"Addresses received drop: {len(op_data)}\n")
    file.write(f"Average amount received: {average_op:.2f} (${average_op_usd:.2f})\n")
    file.write(f"Median amount received: {median_op:.2f} (${median_op_usd:.2f})\n")
    file.write(f"Total drop distribution: {total_op_drop} (${total_drop_usd:.2f})\n")
