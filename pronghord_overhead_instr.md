# Replicating Table 4 and 5

- [x] Understand [README.md](file:///home/natha/projects/239/pronghorn-artifact/README.md) instructions for Table 4 and 5.
- [x] Identify functions executed in `basic` run.
- [x] Analyze [cost-analysis/table_4.py](file:///home/natha/projects/239/pronghorn-artifact/cost-analysis/table_4.py) and [cost-analysis/table_5.py](file:///home/natha/projects/239/pronghorn-artifact/cost-analysis/table_5.py).
- [x] Explain the steps to replicate the tables for `bfs` and `mst` only.

### Replicating Tables 4 and 5 for a `basic` run

Since only `bfs` and `mst` are executed in a `basic` test run, you should only focus on these benchmarks.

#### Table 4 (Checkpoint & Restore Overhead)
1. Ensure the function image is built. For your case, deploy directly with:
   `faas-cli deploy --image=potatocabage/bfs --name=bfs --env=ENV=cold,true,1`
2. Wait for the OpenFaaS pod containing the function container to start running:
   `kubectl get pods -n openfaas-fn`
3. Execute the evaluation script directly inside the container by streaming it through `stdin` (since `tar` is missing, `kubectl cp` won't work):
   `kubectl exec -i -n openfaas-fn $(kubectl get pods -n openfaas-fn -l faas_function=bfs -o jsonpath='{.items[0].metadata.name}') -- python3 - < cost-analysis/table_4.py`
4. The output will immediately print the *dump time*, *restore time*, and *checkpoint size* for `bfs`.
5. Remove `bfs` (`faas-cli remove bfs`) and repeat the exact same deployment and testing workflow for `mst` (`--image=potatocabage/mst --name=mst`).

#### Table 4 (Number of requests to Reach Optimal State)
1. Look into the generated results CSV files from your successful `./run.sh basic` test (e.g. [data/python-basic.csv](file:///home/natha/projects/239/pronghorn-artifact/data/python-basic.csv)).
2. Run the notebook [cost-analysis/evaluation_analysis.ipynb](file:///home/natha/projects/239/pronghorn-artifact/cost-analysis/evaluation_analysis.ipynb), ensuring you are loading your specific [data/python-basic.csv](file:///home/natha/projects/239/pronghorn-artifact/data/python-basic.csv) inside the dataset loading cell instead of the dataset from the full suite evaluation. The visualizations there will demonstrate the required number of requests.

#### Table 5 (Storage & Network Bandwidth Overhead)
1. Open the file [cost-analysis/table_4_results.json](file:///home/natha/projects/239/pronghorn-artifact/cost-analysis/table_4_results.json). Eviscerate its contents and replace it with just the records for `BFS` and `MST`. Update their `checkpoint_size` fields with the accurate sizes you gathered from running the Table 4 script.
2. Run [table_5.py](file:///home/natha/projects/239/pronghorn-artifact/cost-analysis/table_5.py) to synthesize the custom results:
   `cd cost-analysis && python3 table_5.py`
3. The printed output translates precisely to what belongs in Table 5.
