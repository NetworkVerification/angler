#!/usr/bin/env python3
# Export Batfish JSON snapshots

from ipaddress import IPv4Address, IPv4Interface, IPv4Network
import json
import os
import sys
from typing import Any
from pybatfish.client.session import Session
from aast.types import TypeAnnotation
import bast.json
from pathlib import Path

from convert import convert_batfish
from query import QueryType
from serialize import Serialize


def initialize_session(snapshot_dir: str, diagnostics: bool = False) -> Session:
    """
    Perform initial Session setup with the given example network
    and the provided snapshot directory and snapshot name.
    :param network: the name of the example network
    """
    bf = Session(host="localhost")
    bf.set_network("example-net")
    bf.init_snapshot(snapshot_dir, "example-snapshot", overwrite=True)
    if diagnostics:
        print("Saving diagnostics for input files...")
        bf.upload_diagnostics(dry_run=True)
    return bf


class AstEncoder(json.JSONEncoder):
    def default(self, obj):
        match obj:
            case set():
                return list(obj)
            case IPv4Address():
                return str(obj)
                # return {
                #     "Begin": str(obj),
                #     "End": str(obj),
                # }
            case IPv4Interface():
                # drop down to the IPv4Address case
                return obj.ip
            case IPv4Network():
                # TODO: add prefix length?
                return {
                    "Begin": str(obj[0]),
                    "End": str(obj[-1]),
                }
            case Serialize():
                return obj.to_dict()
            case TypeAnnotation():
                return obj.value
            case _:
                # Let the base class default method raise the TypeError
                return json.JSONEncoder.default(self, obj)


def save_json(output: Any, path: Path | str):
    with open(path, "w") as jsonout:
        json.dump(output, jsonout, cls=AstEncoder, sort_keys=True, indent=2)


USAGE = f"""
{os.path.basename(__file__)} : wrapper around pybatfish to extract ast components

Usage: {os.path.basename(__file__)} [-h] [dir|file] [-d] [-q query] [-t] [outfile]

-h          Print usage
-d          Request local diagnostics when initializing pybatfish session
-q query    Add query information based on the given query ("reachable", "valleyfree", "hijack")
-t          Add temporal interfaces
dir         A snapshot directory to provide to pybatfish
file        A JSON file to parse the AST of
outfile     A location to save the output JSON to (defaults to dir.json or file.angler.json)
"""

if __name__ == "__main__":
    match sys.argv[1:]:
        case ["-h" | "--help" | "-?"]:
            print(USAGE)
        case [p, *tl] if os.path.isdir(p):
            bf = initialize_session(p, "-d" in tl)
            output = bast.json.query_session(bf)
            print("Completed Batfish JSON queries.")
            match tl:
                case [] | ["-d"]:
                    # use Path to sanitize the string
                    out_path = Path(p).with_suffix(".json").name
                case ["-d", q]:
                    out_path = q
                case _:
                    out_path = tl[0]
            save_json(output, out_path)
        case [p, *tl] if os.path.isfile(p):
            with open(p) as fp:
                output = json.load(fp)
            bf_ast = bast.json.BatfishJson.from_dict(output)
            print("Successfully parsed Batfish AST!")
            match tl:
                case []:
                    in_path = Path(p)
                    out_path = in_path.with_stem(f"{in_path.stem}.angler")
                    query = None
                case ["-q", q, address, *tl]:
                    in_path = Path(p)
                    out_path = in_path.with_stem(f"{in_path.stem}.angler")
                    query = QueryType(q).to_query(IPv4Address(address), "-t" in tl)
                case _:
                    out_path = tl[0]
                    query = None
            a_ast = convert_batfish(bf_ast, query)
            save_json(a_ast, out_path)
        case _:
            print(USAGE)
