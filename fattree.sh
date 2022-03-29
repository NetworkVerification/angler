#!/usr/bin/env zsh
# generate fattree benchmarks
# arguments should be a sequence of ints for the number of pods each fattree has

for k in "$@"; do
    # determine the address to route to
    # we compute addresses from the nodes, so
    # this means we have to get the number of the last node
    # of the k-pod fattree
    # (hence the -1 since we start at node 0)
    (( v = (5 * k * k) / 4 - 1))
    (( x = v / 256 ))
    (( y = v % 256 ))
    address="70.$x.$y.1"
    python angler.py "sp$k.json" -q reachable $address -t
done
