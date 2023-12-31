#!/bin/bash

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
echo $DIR

# Configuring yaml files
if [ -f multipass.yaml ]; then
    rm multipass.yaml
fi
touch multipass.yaml
echo "# multipass.yaml" >> multipass.yaml
echo "ssh_authorized_keys:" >> multipass.yaml
echo "  - $(cat ~/.ssh/id_rsa.pub)" >> multipass.yaml

# Define the directory path
data_dir="volumes/data"
# Check if the directory exists
if [ -d "$data_dir" ]; then
    # Directory exists, so delete it
    echo "Deleting existing directory: $data_dir"
    rm -rf "$data_dir"
fi
mkdir -p "$data_dir"
if [ -f minio.yaml ]; then
    rm minio.yaml
fi
echo "apiVersion: v1
kind: Namespace
metadata:
  name: stores
  labels:
    name: stores
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: minio
  namespace: stores
spec:
  selector:
    matchLabels:
      app: minio
  replicas: 1
  template:
    metadata:
      labels:
        app: minio
    spec:
      containers:
      - name: minio
        image: quay.io/minio/minio:latest
        command:
        - /bin/bash
        - -c
        args:
        - minio server /data --console-address :9090
        ports:
        - containerPort: 9000
        volumeMounts:
        - mountPath: /data
          name: localvolume
      nodeSelector:
        kubernetes.io/hostname: pronghorn" >> minio.yaml
data_dir="$DIR/volumes/data"
echo "      volumes:
        - name: localvolume
          hostPath:
            path: $(echo $data_dir)
            type: DirectoryOrCreate" >> minio.yaml


# Default configuration
nodes=3
cpus=2
memory="8G"
disk_size="50G"

# Bootstrap The Nodes
for node in $(seq 1 $nodes)
do
  if [ $node -eq 1 ];
  then
    echo "Deploying the master node"
    multipass launch --cpus $cpus --memory $memory --disk $disk_size --name pronghorn 20.04 --cloud-init multipass.yaml
    echo "Master node deployed"
  else
    echo Launching the worker nodes
    multipass launch --cpus $cpus --memory $memory --disk $disk_size --name "pronghorn-m0$node" 20.04 --cloud-init multipass.yaml   
    echo "Worker node $node deployed"
  fi
done

# Deploy Kubernetes Cluster
k3sup install --ip $(multipass info pronghorn | grep IPv4 | awk '{print $2}') --user ubuntu --k3s-extra-args '--cluster-init'
for node in $(seq 2 $nodes)
do
    k3sup join --ip $(multipass info pronghorn-m0$node | grep IPv4 | awk '{print $2}') --server-ip $(multipass info pronghorn | grep IPv4 | awk '{print $2}') --user ubuntu
done

echo "[Completed] Kuberentes cluster created with $nodes nodes, $cpus CPUs, $memory MB memory and $disk_size disk size."

# Set correct contexts
export KUBECONFIG="$DIR/kubeconfig"

# Install OpenFaaS
arkade install openfaas --set faasnetes.image=skharban/faas-netes:privileged-containers &> /dev/null
if kubectl get namespace openfaas &> /dev/null; then
    echo "[Completed] OpenFaaS Installed."
else
    echo "[Error] OpenFaaS Installation Unsuccessful."
    exit 1
fi

# Ensure gateway rollout is complete
while true; do
    pod_list=$(kubectl get pods -n openfaas | grep gateway)
    if [ -n "$pod_list" ]; then
        status=$(echo "$pod_list" | grep Running)
        if [ -n "$status" ]; then
            echo "[Completed] Gateway Rollout"
            break;
        else
            echo "[Waiting] Gateway Rollout In Progress"
            sleep 10
        fi
    else
        echo "[Error] No Gateway Pod Found"
        exit 1
    fi
done

# Port forward OpenFaaS Gateway
nohup kubectl port-forward -n openfaas svc/gateway 8080:8080 &

sleep 5s

# Export OpenFaaS Password
export OPENFAAS_PASSWORD=$(kubectl get secret -n openfaas basic-auth -o jsonpath="{.data.basic-auth-password}" | base64 --decode; echo)
echo $OPENFAAS_PASSWORD > .credentials

# Authenticate OpenFaaS
cat .credentials | faas-cli login --username admin --password-stdin

# Deploy MinIO (Object Store)
kubectl apply -f $DIR/minio.yaml
kubectl apply -f $DIR/minio-service.yaml

# Deploy Database
kubectl apply -f $DIR/database/pod.yaml

# Check Database deployment
attempts=0
pod_name=$(kubectl get pod -n stores -o jsonpath='{.items[0].metadata.name}')

while [[ "$attempts" -lt 3 ]]; do
    pod_status=$(kubectl get pod -n stores $pod_name -o jsonpath='{.status.phase}')
    if [[ "$pod_status" == "Running" ]]; then
        echo "[Completed] Database Deployed on Cluster."
        break
    else
        echo "[Waiting] Database Deployment In Progress"
        sleep 10
        attempts=$((attempts+1))
    fi
done

if [[ "$attempts" -eq 3 ]]; then
    echo "[Error] Database Deployment Failed."
    exit 1
fi

# Check MinIO deployment
attempts=0
pod_name=$(kubectl get pod -n stores -o jsonpath='{.items[1].metadata.name}')

while [[ "$attempts" -lt 3 ]]; do
    pod_status=$(kubectl get pod -n stores $pod_name -o jsonpath='{.status.phase}')
    if [[ "$pod_status" == "Running" ]]; then
        echo "[Completed] MinIO Deployed on Cluster."
        break
    else
        echo "[Waiting] MinIO Deployment In Progress"
        sleep 10
        attempts=$((attempts+1))
    fi
done

if [[ "$attempts" -eq 3 ]]; then
    echo "[Error] MinIO Deployment Failed."
    exit 1
fi

# Check if MinIO service is running
attempts=0

while [[ "$attempts" -lt 3 ]]; do
    service_ip=$(kubectl get svc minio-svc -n stores -o jsonpath='{.spec.clusterIP}')
    if [[ -n "$service_ip" ]]; then
        echo "[Completed] MinIO Service Deployed."
        break
    else
        echo "[Waiting] MinIO Service Deployment In Progress"
        sleep 10
        attempts=$((attempts+1))
    fi
done

if [[ "$attempts" -eq 3 ]]; then
    echo "[Error] MinIO Service Deployment Failed."
    exit 1
fi

nohup kubectl port-forward -n stores svc/minio-svc 9000:9000 &

mc alias set myminio http://localhost:9000 minioadmin minioadmin
