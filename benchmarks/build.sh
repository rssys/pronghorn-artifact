#!/bin/bash

# List of all functions
pypy_functions=( bfs dfs dynamic-html mst pagerank compress upload thumbnail video )
jvm_functions=( matrix-multiplication simple-hash word-count html-rendering )

joined_pypy=$(IFS=','; echo "${pypy_functions[*]}")
joined_jvm=$(IFS=','; echo "${jvm_functions[*]}")

bash build_runtime.sh $joined_pypy pypy
bash build_runtime.sh $joined_jvm jvm