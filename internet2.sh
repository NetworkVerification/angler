#!/usr/bin/env sh
# Script to run angler.py to generate the internet2 benchmark.

docker build -t angler .
# run angler to extract the .json file and then create the .angler.json file
# we do not use -q bte as it's buggy
docker compose run -iTv"${PWD}:/results" angler sh -s <<EOF
python3 angler.py examples/INTERNET2
python3 angler.py -b INTERNET2.json
cp INTERNET2.json /results
cp INTERNET2.angler.json /results
EOF
docker compose down
