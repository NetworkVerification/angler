#!/usr/bin/env python3
# Export Batfish JSON snapshots
#
import json
import os
import sys
from typing import Any
from pybatfish.client.session import Session
from pybatfish.datamodel.answer import TableAnswer

from bat_ast import BatfishJson, RoutingPolicy, StructureType


def initialize_session(snapshot_dir: str):
    """
    Perform initial Session setup with the given example network
    and the provided snapshot directory and snapshot name.
    :param network: the name of the example network
    """
    bf = Session(host="localhost")
    bf.set_network("example-net")
    bf.init_snapshot(snapshot_dir, "example-snapshot", overwrite=True)
    return bf


def get_node_properties(session: Session) -> TableAnswer:
    """
    Return the properties of the network nodes.
    """
    return session.q.nodeProperties().answer()


def get_layer3_edges(session: Session) -> TableAnswer:
    """
    Return the layer 3 edges of the network.
    """
    return session.q.layer3Edges().answer()


def get_named_structures(session: Session) -> TableAnswer:
    """
    Return the named structures of the network.
    """
    return session.q.namedStructures().answer()


def collect_rows(answer: TableAnswer) -> list[dict[str, Any]]:
    """
    Return the rows of the answers in the given TableAnswer.
    """
    return [row for a in answer["answerElements"] for row in a["rows"]]


def load_json(json_path: str) -> dict[str, Any]:
    """
    Load a JSON file.
    Has three parts: topology, policy and declarations.
    """
    with open(json_path) as fp:
        return json.load(fp)


USAGE = f"""
{os.path.basename(__file__)} : wrapper around pybatfish to extract ast components

Usage: {os.path.basename(__file__)} [-h] [dir|file]

-h      Print usage
dir     A snapshot directory to provide to pybatfish
file    A JSON file to parse the AST of
"""

if __name__ == "__main__":
    match sys.argv[1:]:
        case ["-h" | "--help" | "-?"]:
            print(USAGE)
        case [p] if os.path.isdir(p):
            bf = initialize_session(p)
            info = {
                "topology": get_layer3_edges,
                "policy": get_node_properties,
                "declarations": get_named_structures,
            }
            output = {k: collect_rows(v(bf)) for k, v in info.items()}
            bf_ast = BatfishJson.from_dict(output)
            print(json.dumps(output, sort_keys=True, indent=2))
        case [p] if os.path.isfile(p):
            output = load_json(p)
            bf_ast = BatfishJson.from_dict(output)
            for decl in bf_ast.declarations:
                if decl.ty is StructureType.ROUTING_POLICY:
                    print(decl.definition.value)
        case _:
            print(USAGE)
