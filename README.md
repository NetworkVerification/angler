# angler

generate a suitable json representation of network behavior for easy consumption
by a variety of network verification tools.
designed to save network verification tool developers from having to work with batfish
directly and fishes out the most relevant information for you.

## approach

angler starts from [batfish](https://github.com/batfish/batfish):
given a configuration directory,
angler queries batfish for some general information about the network
using [pybatfish](https://github.com/batfish/pybatfish),
exporting batfish's IR as JSON.
it then simplifies this information using a series of transformations to output
a condensed JSON representation of the network control plane,
for other tools to parse and use.

## how to use

### installation

the easiest way to use angler is via [poetry](python-poetry.org): simply run `poetry install` from the base directory
to set up a virtual environment you can use for running angler.

### running

once the poetry environment has been set up, you can just use `poetry run` to run angler.
note that to read configurations with batfish, you must run the batfish docker service.

```sh
# start the batfish service (e.g. with a container manager of your choice)
docker start batfish
# or: docker run --name batfish -v batfish-data:/data -p 8888:8888 -p 9997:9997 -p 9996:9996 batfish/allinone
# then dump an example network config to JSON
poetry run python -m angler examples/BDD1
# this creates a BDD1.json file for you to inspect at your leisure,
# or convert to the internal angler IR
poetry run python -m angler BDD1.json
```
