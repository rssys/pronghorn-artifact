#!/bin/bash

if [ "$1" == "basic" ]; then
  pypy_functions="bfs"
  python3 synthetic_run.py 500 200 pypy basic $pypy_functions
elif [ "$1" == "suite" ]; then
  jvm_functions="matrix-multiplication simple-hash word-count html-rendering"
  python3 synthetic_run.py 500 100 jvm suite $jvm_functions
elif [ "$1" == "evaluation" ]; then
  pypy_functions="bfs dfs dynamic-html mst pagerank compress upload thumbnail video"
  python3 synthetic_run.py 500 200 pypy evaluation $pypy_functions

  jvm_functions="matrix-multiplication simple-hash word-count html-rendering"
  python3 synthetic_run.py 500 100 jvm evaluation $jvm_functions

  # Remove the state store to avoid conflicts with the next run
  cd ./database
  make redeploy-k8s

  # Remove the old checkpoints
  mc rb myminio/checkpoints --force
else
  echo "Usage: $0 [basic|suite|evaluation]"
  exit 1
fi
