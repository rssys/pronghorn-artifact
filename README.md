# Pronghorn Artifact Evaluation

Pronghorn is a snapshot orchestrator for serverless platforms, which accelerates the average execution latency of deployed functions.

## Getting Started

### Prerequisite

Hardware Requirements: We recommend employing a bare-metal machine with _A_ x86-64 CPUs, _B_ GB of memory, and _Z_ GB of storage.

Software Requirements: 

- Linux (Ubuntu 22.04 Recommended).
- Docker Engine v20.10.12 or higher. 
- Kubernetes Server v1.21.1 or higher.

Note: Please make sure to login to your DockerHub account on the testbed to make sure that the system assumes DockerHub as the image registry.

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

- If any components of the toolchain show up as uninstalled post installation, make sure that you add the arkade binary directory to your PATH variable `export PATH=$PATH:$HOME/.arkade/bin/`
- Make sure to run `ssh-keygen` before running the deployment script on newly provisioned testbed instances to ensure that `k3sup` and `multipass` have access to the host's public key.
- Make sure to install the `build-essential` package using `sudo apt install build-essential`.

### Build

⏰ Estimated time: X machine minutes + 0 human minutes.

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


⚠️ Navigating Potential Build Errors

## Directory Structure

```
📦 
├─ .gitignore
├─ README.md
├─ agent-java
├─ agent-python
├─ benchmarks
│    ├─ java
│    │  ├─ html-rendering
│    │  ├─ json-parsing
│    │  ├─ matrix-multiplication
│    │  ├─ simple-hash
│    │  └─ word-count
│    ├─ python
│    │ ├─ bfs
│    │ ├─ compress
│    │ ├─ dfs
│    │ ├─ dynamic-html
│    │ ├─ mst
│    │ ├─ pagerank
│    │ ├─ thumbnail
│    │ ├─ upload
│    │ ├─ video
│    ├─ build_function.sh
│    ├─ build_runtime.sh
│    ├─ build_suite.sh
├─ database
├─ deploy.sh 
├─ minio-service.yaml
├─ minio.yaml
└─ multipass.yaml
```
© generated by [Project Tree Generator](https://woochanleee.github.io/project-tree-generator)