"""
Functionality for parsing Batfish's JSON representation back into an AST.
All classes here are essentially just organized data: the code is written
(perhaps not very Pythonically) to allow us to decode an entire JSON file
directly into a nested hierarchy of Python dataclasses.
Once those are arranged, we can then write code to access the dataclasses
and return the relevant components.
The main benefit of using these dataclasses rather than simply parsing the
JSON directly is that the static classes expect certain data: if the JSON
output is malformed or our implementation no longer aligns with Batfish,
we want to fail to decode the file and return an error immediately.

:author: Tim Alberdingk Thijm <tthijm@cs.princeton.edu>
"""
