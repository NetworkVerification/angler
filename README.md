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

you can get all the necessary dependencies via the provided `requirements.txt` file.

```sh
# ... set up your virtualenv ...
pip install -r requirements.txt
```

### running

```sh
# start the batfish service (e.g. with a container manager of your choice)
docker start batfish
# then dump an example network config to JSON
python angler.py examples/BDD1
# this creates a BDD1.json file for you to inspect at your leisure,
# or convert to the internal angler IR
python angler.py bdd.json
```

## to-dos

- [ ] ensure that we export all relevant batfish information for general examples
- [x] implement AST nodes for all basic batfish expressions
- [x] define a simplified angler JSON specification
- [ ] write interpreter from batfish expressions into angler JSON
- [ ] export angler JSON; write parsers for it in other verification tools
