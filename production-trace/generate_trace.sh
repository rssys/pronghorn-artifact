#!/bin/sh

bash process_trace.sh -t trace.csv -d d07 -b 720 -e 735

python3 post_process_trace.py 75

rm trace.csv

mv *.csv trace.csv