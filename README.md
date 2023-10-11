[https://drive.google.com/uc?export=view&id=1kDkm_ZBX0KJkOo5E74d03pGjucAD2v2r]

# Pronghorn Artifact Evaluation

Pronghorn is a snapshot orchestrator for serverless platforms, which accelerates the average execution latency of deployed functions.

## Getting Started

### Prerequisite

Hardware Requirements: We recommend employing a bare-metal machine with 8 x86-64 CPUs, 32 GB of memory, and 256 GB of storage.

Software Requirements: 

- Linux (Ubuntu 22.04 Recommended).
- Docker Engine v20.10.12 or higher. 
- Kubernetes Server v1.21.1 or higher.

Note: Please make sure to login to your DockerHub account on the testbed to make sure that the Kubernetes can pull the function images from the appropriate image registry.

Toolchain Requirements:

- Multipass v1.12.2 or higher.
- Arkade v0.8.28 or higher.
- Helm v3.5.2 or higher.
- Kubectl v1.2.22 or higher.
- k3sup v0.11.3 or higher.
- faas-cli v0.14.2 or higher.

```bash
sudo snap install multipass

curl -sLS https://get.arkade.dev | sudo sh

arkade get helm kubectl k3sup faas-cli

export PATH=$PATH:$HOME/.arkade/bin/
```

Configuration Requirements:

- Enable Docker Buildkit Builder by adding the following to the `~/.docker/config.json` file and then restart the docker daemon.

```bash
{
    ...
    "experimental": true,
    ...
}
```

- Create the Docker Builder

```bash
docker buildx create --use --name pronghorn-builder --buildkitd-flags '--allow-insecure-entitlement security.insecure --allow-insecure-entitlement network.host'

docker buildx inspect --bootstrap
```

- Create a link to Pronghorn's template registry for OpenFaaS

```bash
export OPENFAAS_TEMPLATE_URL=https://github.com/Alphacode18/templates/
```

### Download

The code can be easily downloaded via:

```bash
git clone https://github.com/rssys/pronghorn-artifact.git
```

### Deployment

⏰ Estimated time: 4 machine minutes + 0 human minutes.

The repository includes a `deploy.sh` script, which automates the process of spinning up and configuring a multi-node kubernetes cluster with our fork of OpenFaaS (an open-source serverless platform), MinIO (an open-source S3-compatible object store), and a lightweight key-value store.

```bash
chmod +x ./deploy.sh

./deploy.sh
```

A successful deployment should look like this:

```bash
user@hostname:~/pronghorn-artifact$ kubectl get pods --all-namespaces
NAMESPACE     NAME                                      READY   STATUS      RESTARTS  AGE
kube-system   coredns-59b4f5bbd5-jf5g7                  1/1     Running     0         Xs
kube-system   helm-install-traefik-ckmq9                0/1     Completed   0         Xs
kube-system   helm-install-traefik-crd-4gxrj            0/1     Completed   0         Xs
kube-system   local-path-provisioner-76d776f6f9-dsv26   1/1     Running     0         Xs
kube-system   metrics-server-7b67f64457-mqz42           1/1     Running     0         Xs
kube-system   svclb-traefik-c9b3d331-485h2              2/2     Running     0         Xs
kube-system   svclb-traefik-c9b3d331-cgkcl              2/2     Running     0         Xs
kube-system   svclb-traefik-c9b3d331-gvjhn              2/2     Running     0         Xs
kube-system   traefik-57c84cf78d-wkfmd                  1/1     Running     0         Xs
openfaas      alertmanager-789c6cccff-kqflv             1/1     Running     0         Xs
openfaas      gateway-7f96594f48-p5gqk                  2/2     Running     0         Xs
openfaas      nats-787c8b658b-494c8                     1/1     Running     0         Xs
openfaas      prometheus-c699bf8cc-zmfm2                1/1     Running     0         Xs
openfaas      queue-worker-5fcbb4f849-wmf7j             1/1     Running     0         Xs
stores        minio-6d5b865db8-9fnwd                    1/1     Running     0         Xs
stores        database-75dc6bb78f-6zr2n                 1/1     Running     0         Xs
```

⚠️ Navigating Potential Deployment Errors

- Make sure to run `ssh-keygen` before running the deployment script on newly provisioned testbed instances to ensure that `k3sup` and `multipass` have access to the host's public key.
- Make sure to install the `build-essential` package using `sudo apt install build-essential`.

### Build

⏰ Estimated time: 15 machine minutes + 0 human minutes.

The repository includes a `benchmarks/build.sh` script, which automates the process of building the images for all the benchmarks and pushes it to the remote image registry.

```bash
cd benchmarks

chmod +x ./build.sh

./build.sh
```

The script will:
- Create the necessary build files for each benchmark.
- Create a docker image for each benchmark.
- Deploy each benchmark and do a sanity check.
- Perform clean up.

A successful build process should look something like this:

```bash
pypy Functions that returned OK:
 - bfs
 - dfs
 - dynamic-html
 - mst
 - pagerank
 - compress
 - upload
 - thumbnail
 - video
pypy Functions that did NOT return OK:

jvm Functions that returned OK:
 - matrix-multiplication
 - simple-hash
 - word-count
 - html-rendering
jvm Functions that did NOT return OK:
```


⚠️ Navigating Potential Build Errors

## Basic Test

⏰ Estimated time: 15 machine minutes + 5 human minutes.

Run the script `./run.sh basic`. This script will automatically run the whole pipeline of Pronghorn for one of the functions in the benchmarks and produce the results for chosen (function, runtime) in a CSV file, which can be used to produce a CDF plot of the latency.

## Suite Test

⏰ Estimated time: 24 machine hours + 5 human minutes.

Run the script `./run.sh suite`. This script will automatically run the whole pipeline of Pronghorn for one of the suites (java or python) in the benchmarks and produce the results in a CSV file, which can be used to produce a CDF plot of the latency.

## Evaluation

⏰ Estimated time: 48 machine hours + 5 human minutes.

Run the script `./run.sh evaluation`. This script will automatically run the whole pipeline of Pronghorn for the entire benchmarking suite and will produce two CSV files. pypy.csv and jvm.csv, which can be utilized to reproduce the figure X and figure Y in the paper.

## Key results in the paper:

Figure 4: The Cumulative Distribution Function (CDF) of end-to-end request latency in microseconds of Python benchmarks (rows) across the evaluated orchestration strategies 
and three different container eviction rates (columns).

Figure 5: The Cumulative Distribution Function (CDF) of end-to-end request latency in microseconds of Java benchmarks (rows) across the evaluated orchestration strategies 
and three different container eviction rates (columns).

Table 4: For each benchmark, the requests taken by Pronghorn to find the optimal snapshot; snapshot sizes; and checkpoint/restore times.

Table 5: For each benchmark, the maximum storage used by Pronghorn’s orchestration strategy, the maximum cumulative network bandwidth used to transfer snapshots, and the baseline values for state-of-the-art.

## Reproducing key results:

### Figures 4 and 5

**Duration:** 30 human-minutes + 48 compute-hour

In this experiment, we conduct a comprehensive evaluation encompassing all benchmarks, strategies, and eviction rates, as presented in Section 5 of the paper.

**Preparation:**
The Pronghorn setup process automatically generates the necessary configurations for this experiment. No additional steps are necessary.

**Execution:**
To initiate the experiment, simply execute the `run.sh` script located in the root directory with the `evaluation` argument. Given the extended duration of this experiment, we advise running the command in the background using a mechanism such as `nohup ./run.sh evaluation &` to ensure uninterrupted execution.

**Results:**
The results will be created as CSV files in the `results/` directory. The `Evaluation.ipynb` plotting script provided in the `figures/` directory can be used to interactively create Figure 4 and Figure 5 of the paper.

### Table 4

**Duration:** 1 human-hour + 1 compute-hour

This experiment enables the assessment of the system’s checkpoint and restore overhead.

**Preparation:**
Deploy any function using `faas-cli deploy --image=USER/workload --name=workload`.

**Execution:**
Copy the script `cost-analysis/table4.py` to the pod created by OpenFaaS. Next, attach to the pod using `kubectl exec -it $pod name -- /bin/sh` and run the script within the pod. Copy the JSON emitted by the program to a file that can be used for the analysis.

**Results:**
If required, this can be done for all functions. However, for convenience, a result JSON file has been attached from our evaluation run. The results provide the numbers for the checkpoint, restore, and snapshot overheads presented in Table 4.

### Table 4

**Duration:** 10 human-minutes + 10 compute-minutes

This experiment quantifies the number of requests needed for Pronghorn to reach an optimal snapshot state.

**Preparation:**
The evaluation run will produce the necessary inputs for this experiment.

**Execution:**
To compute and display the results, simply execute the `cost-analysis/evaluation cost.ipynb` notebook.

**Results:**
The output obtained from the notebook can be directly compared with Table 4 of the paper.

### Table 5

**Duration:** 10 human-minutes + 10 compute-minutes

This experiment allows evaluating the storage and network bandwidth usage of Pronghorn.

**Preparation:**
The data collected for E2 will produce the necessary inputs for this experiment.

**Execution:**
To compute and display the results, simply run the `cost-analysis/table 5.py` notebook.

**Results:**
The output obtained from the notebook can be directly compared with Table 5 of the paper.


## Directory Structure

```
📦 
├─ .gitignore
├─ README.md
├─ agent-java
├─ agent-python
├─ benchmarks
│  ├─ java
│  │  ├─ html-rendering
│  │  ├─ matrix-multiplication
│  │  ├─ simple-hash
│  │  └─ word-count
│  ├─ python
│  │  ├─ bfs
│  │  ├─ compress
│  │  ├─ dfs
│  │  ├─ dynamic-html
│  │  ├─ mst
│  │  ├─ pagerank
│  │  ├─ thumbnail
│  │  ├─ upload
│  │  └─ video
├─ database
├─ deploy.sh
├─ minio-service.yaml
├─ minio.yaml
├─ multipass.yaml
├─ run.sh
└─ synthetic_run.py
```
© generated by [Project Tree Generator](https://woochanleee.github.io/project-tree-generator)
