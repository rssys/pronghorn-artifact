import json

# Load the JSON data
with open("table_5.json", "r") as f:
    data = json.load(f)

# Set checkpoint pool
checkpoint_pool = 12

# Set eviction rates
eviction_rate = 4  # this is just a placeholder value

results = {}

for benchmark, benchmark_data in data.items():
    checkpoint_size = benchmark_data["checkpoint_size"]

    # Calculate the storage overhead
    storage_overhead = checkpoint_size * checkpoint_pool

    # Calculate the network bandwidth overhead
    total_requests = 500
    network_bandwidth_overhead = (total_requests / eviction_rate) * 2 * checkpoint_size

    results[benchmark] = {
        "storage_overhead": f"{storage_overhead:.1f} MB",
        "network_bandwidth_overhead": f"{network_bandwidth_overhead:.1f} MB",
    }

# Print the results
for benchmark, overheads in results.items():
    print(f"\nBenchmark: {benchmark}")
    for overhead_type, overhead_value in overheads.items():
        print(f"{overhead_type}: {overhead_value}")
