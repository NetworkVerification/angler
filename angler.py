#!/usr/bin/env python3
"""
A tool for exporting [Batfish](https://www.batfish.org/)'s internal AST to a simpler format.
The AST can then be consumed by a separate tool which defines the semantics.

Operates in two passes:
1. Using Batfish's [pybatfish](https://batfish.readthedocs.io/en/latest/index.html) API,
   given a directory of configurations CONFIGS,
   extract all relevant routing information as statements in Batfish's AST,
   and save it in a JSON file "CONFIGS.json".
2. Convert the "CONFIGS.json" file to use Angler's [alternative representation](`aast`).
   This representation, while also in JSON, replaces some of Batfish's highly-specific structures
   with simpler, more generic imperative commands, via an AST traversal.
   Save the resulting Angler AST as a JSON file "CONFIGS.angler.json".

Given a directory of configurations, **angler** will perform both passes together,
unless the "--batfish-only" flag is given, in which case only pass 1 is performed.
Given a "CONFIGS.json" file, **angler** will perform pass 2.
"""

import argparse
from ipaddress import IPv4Address, IPv4Interface, IPv4Network
import json
import os
import pathlib
from typing import Any
from pybatfish.client.session import Session
from aast.types import TypeAnnotation
import bast.json
import convert
from pathlib import Path
from serialize import Serialize


def initialize_session(snapshot_dir: Path, diagnostics: bool = False) -> Session:
    """
    Perform initial Session setup with the given example network
    and the provided snapshot directory and snapshot name.
    :param network: the name of the example network
    """
    bf = Session(host="localhost")
    bf.set_network("example-net")
    # convert the path to a string so that it's correctly identified by batfish
    # for whatever reason, passing in a pathlib.Path causes a problem
    bf.init_snapshot(str(snapshot_dir), "example-snapshot", overwrite=True)
    if diagnostics:
        print("Saving diagnostics for input files...")
        bf.upload_diagnostics(dry_run=True)
    return bf


class AstEncoder(json.JSONEncoder):
    """
    An extension of the `json.JSONEncoder` for angler.
    Adds support for `ipaddress` expressions, `Serialize`-able objects
    and `TypeAnnotation`s.
    """

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


def _save_json(output: Any, path: Path | str):
    with open(path, "w") as jsonout:
        json.dump(output, jsonout, cls=AstEncoder, sort_keys=True, indent=2)


def main():
    parser = argparse.ArgumentParser(
        f"{os.path.basename(__file__)}", description="extracts Batfish AST components"
    )
    parser.add_argument(
        "-D",
        "--diagnostics",
        action="store_true",
        help="Request local diagnostics when initializing pybatfish session",
    )
    parser.add_argument(
        "-b",
        "--simplify-bools",
        action="store_true",
        help="Simplify AST expressions according to rules of boolean logic",
    )
    parser.add_argument(
        "-B",
        "--batfish-only",
        action="store_true",
        help="Only extract the Batfish AST; do not convert to Angler representation",
    )
    parser.add_argument(
        "path",
        type=pathlib.Path,
        help="A snapshot directory to pass to pybatfish, or a JSON file obtained after reading such a directory",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="A location to save the output JSON to (defaults to [path].json or [path].angler.json)",
    )
    args = parser.parse_args()
    if os.path.isdir(args.path):
        bf = initialize_session(args.path, args.diagnostics)
        json_data = bast.json.query_session(bf)
        print("Completed Batfish JSON queries.")
        out_path = (
            Path(args.path).with_suffix(".json").name
            if args.output is None
            else args.output
        )
        _save_json(json_data, out_path)
    else:
        with open(args.path) as fp:
            json_data = json.load(fp)
        out_path = (
            args.path.with_stem(f"{args.path.stem}.angler")
            if args.output is None
            else args.output
        )
    # if we were given a file and the --batfish-only flag is not set, then convert
    if os.path.isfile(args.path) or not args.batfish_only:
        bf_ast = bast.json.BatfishJson.from_dict(json_data)
        print("Successfully parsed Batfish AST!")
        a_ast = convert.convert_batfish(bf_ast, simplify=args.simplify_bools)
        _save_json(a_ast, out_path)


if __name__ == "__main__":
    main()
