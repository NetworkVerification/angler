#!/usr/bin/env bash
# Given a directory, run angler on every config directory within the directory

INPUTDIR=$1

for configs in $(find $INPUTDIR -type d -mindepth 1 -maxdepth 1); do
    poetry run python -m angler --simplify-bools --full-run $configs
done
