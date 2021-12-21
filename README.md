# angler

generate a suitable json representation of network behavior for easy consumption
by a variety of network verification tools.
designed to save network verification tool developers from having to work with batfish
directly and fishes out the most relevant information for you.

## approach

angler starts from [batfish](https://github.com/batfish/batfish): given a configuration directory,
angler queries batfish for some general information about the network using [pybatfish](https://github.com/batfish/pybatfish),
exporting batfish's IR as JSON.
it then simplifies this information using a series of transformations to output
a condensed JSON representation of the network control plane,
which can be parsed by other tools.

## to-dos

- [ ] ensure that all relevant batfish information is exported for general examples
- [ ] implement AST nodes for all basic batfish expressions
- [ ] define a simplified angler JSON specification
- [ ] write interpreter from batfish expressions into angler JSON
- [ ] export angler JSON; write parsers for it in other verification tools
