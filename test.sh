#!/bin/bash

set -ex 
while true; do
    curl --noproxy "*" http://127.0.0.1:8080/
done
