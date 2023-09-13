#!/bin/bash

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
echo $DIR

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
k3sup install --ip $(multipass info pronghorn | grep IPv4 | awk '{print $2}') --user ubuntu --k3s-extra-args '--cluster-init'  --ssh-key ~/.ssh/id_rsa
for node in $(seq 2 $nodes)
do
    k3sup join --ip $(multipass info pronghorn-m0$node | grep IPv4 | awk '{print $2}') --server-ip $(multipass info pronghorn | grep IPv4 | awk '{print $2}') --user ubuntu
done

echo "[Completed] Kuberentes cluster created with $nodes nodes, $cpus CPUs, $memory MB memory and $disk_size disk size."

# Set correct contexts
export KUBECONFIG="$DIR/kubeconfig"
echo "Remember to export KUBECONFIG=\"$DIR/kubeconfig\""

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
kubectl port-forward -n openfaas svc/gateway 8080:8080 & 

# Export OpenFaaS Password
export OPENFAAS_PASSWORD=$(kubectl get secret -n openfaas basic-auth -o jsonpath="{.data.basic-auth-password}" | base64 --decode; echo)
echo $OPENFAAS_PASSWORD > .credentials

# Authenticate OpenFaaS
cat .credentials | faas-cli login --username admin --password-stdin

# Deploy MinIO (Object Store)
sed -e "s|DIR|$DIR|" $DIR/yaml/minio.yaml | kubectl apply -f -
kubectl apply -f $DIR/yaml/minio-service.yaml

# Deploy Database
cd ~/pronghorn-artifact/database
make build-docker
cd $DIR
sed -e "s|DIR|$DIR|" $DIR/database | kubectl apply -f -
kubectl apply -f $DIR/database/pod.yaml

# Check MinIO deployment
attempts=0
pod_name=$(kubectl get pod -n stores -o jsonpath='{.items[0].metadata.name}')

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
