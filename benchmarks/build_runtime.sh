#!/bin/bash

# Functions
function_string=$1
IFS=', ' read -r -a functions <<< "$function_string"

# Platform type: pypy or jvm
platform=$2

# User
user=skharban

# Directory of the script
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"

# Arrays to store the results
ok_functions=()
not_ok_functions=()

# Function to build Docker images
build_docker_image() {
  identifier=$1
  if [ $platform == "pypy" ]; then
    build_folder="."
    function_service="agent-python"
  else
    build_folder="."
    function_service="agent-java"
  fi

  faas-cli build --shrinkwrap -f "${identifier}.yml"

  # List of identifiers where you want to use a separate Dockerfile
  special_identifiers=("thumbnail" "video" "html-rendering" "json-parsing" "word-count")

  if [[ " ${special_identifiers[@]} " =~ " ${identifier} " ]]; then
    rm "${build_folder}/build/${identifier}/Dockerfile"
    mv "${build_folder}/build/${identifier}/function/Dockerfile" "${build_folder}/build/${identifier}/"
  fi

  echo "[$identifier] Injecting function-service..."
  rm -rf "${build_folder}/build/${identifier}/function-service" && echo "[$identifier] Service Deleted"
  cp -r $DIR/../${function_service} "${build_folder}/build/${identifier}" && echo "[$identifier] Service Copied"
  mv "${build_folder}/build/${identifier}/${function_service}" "${build_folder}/build/${identifier}/function-service" && echo "[$identifier] Service Renamed"

  echo "[$identifier] Building image..."
  docker buildx build --allow security.insecure,network.host -t "$user/${identifier}:latest" --push "${build_folder}/build/${identifier}" > /dev/null 2>&1
  echo "[$identifier] Image built and pushed."
  docker pull $user/${identifier}:latest > /dev/null 2>&1
  echo "[$identifier] Image pulled."
}

# Function to deploy and test Docker images
deploy_test_function() {
  identifier=$1

  echo "[$identifier] Deploying function..."
  faas-cli deploy --image=$user/${identifier} --name=${identifier} --env STRATEGY=cold EVICTIONS=True > /dev/null 2>&1
  echo "[$identifier] Function deployed."

  sleep 5s

  status_code=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8080/function/${identifier}?mutability=0)
  echo "[$identifier] Status code: $status_code"

  if [[ "$status_code" == 200 ]] ; then
    echo "[$identifier] OK"
    ok_functions+=("$identifier")
  else
    echo "[$identifier] NOT OK"
    not_ok_functions+=("$identifier")
  fi

  faas-cli remove ${identifier} > /dev/null 2>&1
  echo "[$identifier] Function removed."

  # Redeploy the Database
  cd ../database && make redeploy-k8s > /dev/null 2>&1
  cd ../benchmarks
  echo "[$identifier] Database redeployed."
  sleep 5s
}

# Iterate over each function and start the build process in the background
for function in "${functions[@]}"; do
  build_docker_image $function &
done

# Wait for all background tasks to finish
wait

echo "All images built and pushed."

# Deploy and test functions sequentially
for function in "${functions[@]}"; do
  deploy_test_function $function
done

# Display the results
echo
echo
echo "$platform Functions that returned OK:"
for func in "${ok_functions[@]}"; do
  echo " - $func"
done

echo "$platform Functions that did NOT return OK:"
for func in "${not_ok_functions[@]}"; do
  echo " - $func"
done