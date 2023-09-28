#!/bin/bash

# Store the initial working directory
INITIAL_DIR=$(pwd)

# create a results directory if not there
DIR="results"
if [ ! -d "$DIR" ]; then
    mkdir $DIR
fi

#List of all functions
functions=( bfs dfs dynamic-html mst pagerank compress upload thumbnail video )

#List of all strategies
strategies=( cold "fixed&request_to_checkpoint=1" "request_centric&max_capacity=12" )

# Loop through each function and for each function each strategy
for function in "${functions[@]}"
do
    for strategy in "${strategies[@]}"
    do
        echo "Processing function: $function"
        echo "Processing strategy: $strategy"

        # Run the python script in the background, capturing its PID
        echo "Starting Python script..."
        # create a filename string
        log_file="$function-$strategy.log"
        if [ "$strategy" == "fixed&request_to_checkpoint=1" ]
        then
            log_file="$function-fixed.log"
        elif [ "$strategy" == "request_centric&max_capacity=12" ]
        then
            log_file="$function-request_centric.log"
        fi
        time python3 azure_run.py -w $function -s $strategy -b openfaas -t trace.csv > $DIR/$log_file
        PID=$!
        echo "Started Python script. PID: $PID"

        # Redeploy using the Makefile
        echo "Redeploying using the Makefile..."
        cd ~/pronghorn-artifact/database
        make redeploy-k8s

        # Get the storage used and then delete all checkpoints from MinIO
        cd ~/pronghorn-artifact/production-trace
        echo "Getting storage used..."
        mc admin info myminio | grep Used > $DIR/$log_file-minio.log

        # Delete all checkpoints
        echo "Deleting all checkpoints from MinIO..."
        mc rb myminio/checkpoints --force

        # Wait for 1 minute
        echo "Waiting for 1 minute..."
        sleep 60s
    done
done