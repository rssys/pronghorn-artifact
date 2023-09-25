import sys
import pandas as pd
import numpy as np

# Read the CSV file into a DataFrame
df = pd.read_csv("trace.csv")

# Group the data by HashOwner and HashFunction, and calculate the unique counts
unique_counts = (
    df.groupby(["HashOwner", "HashFunction"]).size().reset_index(name="Count")
)

# Calculate the desired percentile (e.g., 50th percentile) of the unique counts
percentile = int(sys.argv[1])
percentile_value = np.percentile(unique_counts["Count"], percentile)

# Filter the (HashOwner, HashFunction) pairs that have a count closest to the calculated percentile
filtered_data = unique_counts[unique_counts["Count"] >= percentile_value].sort_values(
    "Count", ascending=True
)
hash_owner_at_percentile = filtered_data.iloc[0]["HashOwner"]
hash_function_at_percentile = filtered_data.iloc[0]["HashFunction"]

# Display results
print(f"HashOwner at {percentile}th percentile: {hash_owner_at_percentile}")
print(f"HashFunction at {percentile}th percentile: {hash_function_at_percentile}")

# Define the filename for the filtered CSV
output_filename = f"trace_{percentile}.csv"

# Filter the original DataFrame based on the selected HashOwner
filtered_df = df[df["HashOwner"] == hash_owner_at_percentile]

# Save the filtered DataFrame to the output CSV file
filtered_df.to_csv(output_filename, index=False)

print(f"Filtered CSV saved as {output_filename}")