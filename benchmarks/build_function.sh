#!/bin/bash

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"

export PATH=$PATH:$(go env GOPATH)/bin

user=skharban

identifier=$1
platform=$2

if [ $platform == "pypy" ]; then
  build_folder="./python"
  function_service="agent-python"
else
  build_folder="./java"
  function_service="agent-java"
fi

echo "Injecting function-service..."
rm -rf "${build_folder}/build/${identifier}/function-service" && echo "Service Deleted"
cp -r $DIR/../../${function_service} "${build_folder}/build/${identifier}" && echo "Service Copied"
mv "${build_folder}/build/${identifier}/${function_service}" "${build_folder}/build/${identifier}/function-service" && echo "Service Renamed"

echo "Building image..."
docker buildx build --allow security.insecure,network.host -t "$user/${identifier}" --push "${build_folder}/build/${identifier}"

sleep 5s

docker pull $user/${identifier}

echo "Deploying function..."
faas-cli deploy --image=$user/${identifier} --name=${identifier}

sleep 5s

#echo "Testing function..."
status_code=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8080/function/${identifier}?mutability=0)

echo $status_code

if [[ "$status_code" == 200 ]] ; then
  echo "OK"
else
  echo "NOT OK"
fi

faas-cli remove ${identifier}

# Wait until the function is removed
while true; do
    # Get the list of functions
    function_list=$(faas-cli list)

    # Check if the function is still in the list
    if [[ $function_list == *"$identifier"* ]]; then
        # If the function is still there, wait for 5 seconds and try again
        echo "Waiting for function '${identifier}' to be removed..."
        sleep 5
    else
        # If the function is not there, break the loop
        echo "Function '${identifier}' has been removed."
        break
    fi
done

echo "Redeploying using the Makefile..."
cd ~/Pronghorn/crud-service
make redeploy-k8s

# Delete all checkpoints
echo "Deleting all checkpoints from MinIO..."
mc rb myminio/checkpoints --force