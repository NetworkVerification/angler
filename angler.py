#!/usr/bin/env python3
# Export Batfish JSON snapshots
#
import json
import os
import sys
from pybatfish.client.session import Session
import bast.json
from pathlib import Path

from bast.structure import RoutingPolicy
from convert import convert_stmt


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
        case [p, *tl] if os.path.isdir(p):
            bf = initialize_session(p)
            output = bast.json.query_session(bf)
            try:
                # will fail if any json elements are not implemented in the AST
                bast.json.BatfishJson.from_dict(output)
                print("Successfully parsed Batfish AST!")
            finally:
                if len(tl) == 0:
                    # use Path to sanitize the string
                    out_path = Path(p).with_suffix(".json").name
                else:
                    out_path = tl[0]
                with open(out_path, "w") as jsonout:
                    json_text = json.dumps(output, sort_keys=True, indent=2)
                    jsonout.write(json_text)
        case [p] if os.path.isfile(p):
            with open(p) as fp:
                output = json.load(fp)
            bf_ast = bast.json.BatfishJson.from_dict(output)
            pr = lambda x: print(type(x))
            # bf_ast.visit(pr)
            for decl in bf_ast.declarations:
                match decl.definition.value:
                    case RoutingPolicy(policyname, statements):
                        print(f"Converting {policyname}")
                        for stmt in statements:
                            s = convert_stmt(stmt)
                            for stmt in s:
                                stmt.visit(pr)
            # print(bf_ast.declarations)
        case _:
            print(USAGE)
