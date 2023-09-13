# Pronghorn Artifact Evaluation

Pronghorn is a snapshot orchestrator for serverless platforms, which accelerates the average execution latency of deployed functions.

## Getting Started

### Prerequisite

Hardware Requirements: We recommend employing a bare-metal machine with _A_ x86-64 CPUs, _B_ GB of memory, and _Z_ GB of storage.

Software Requirements: 

- Linux (Ubuntu 22.04 Recommended).
- Docker Engine v20.10.12 or higher.
- Kubernetes Server v1.21.1 or higher.

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

### Download

The code can be easily downloaded via:

```bash
git clone https://github.com/rssys/pronghorn-artifact.git
```

### Deployment

⏰ Estimated time: _X_ machine minutes + _Y_ human minutes.

The repository includes a `deploy.sh` script, which automates the process of spinning up and configuring a multi-node kubernetes cluster with our fork of OpenFaaS (an open-source serverless platform), MinIO (an open-source S3-compatible object store), and a lightweight key-value store.

```bash
chmod +x ./deploy.sh

./deploy.sh
```