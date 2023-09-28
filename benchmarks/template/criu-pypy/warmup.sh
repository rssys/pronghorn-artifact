#!/bin/sh

while true; do
    (python3 service/main.py) || true
    (killall pypy3) || true
    (kill -9 $(pgrep pypy3)) || true
done
