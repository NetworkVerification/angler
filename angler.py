#!/usr/bin/env python3
# Export Batfish JSON snapshots

import argparse
from ipaddress import IPv4Address, IPv4Interface, IPv4Network
import json
import os
import pathlib
from typing import Any
from pybatfish.client.session import Session
from aast.types import TypeAnnotation
from aast.program import Program
import bast.json
from pathlib import Path

from convert import convert_batfish
from query import QueryType, add_query
from serialize import Serialize


def initialize_session(snapshot_dir: Path, diagnostics: bool = False) -> Session:
    """
    Perform initial Session setup with the given example network
    and the provided snapshot directory and snapshot name.
    :param network: the name of the example network
    """
    bf = Session(host="batfish")
    bf.set_network("example-net")
    # convert the path to a string so that it's correctly identified by batfish
    # for whatever reason, passing in a pathlib.Path causes a problem
    bf.init_snapshot(str(snapshot_dir), "example-snapshot", overwrite=True)
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
        help="Simplify AST expressions according to rules of boolean logic.",
    )
    parser.add_argument(
        "-q",
        "--query",
        type=QueryType,
        help="Specify a verification query to instrument the network with.",
    )
    parser.add_argument(
        "-d",
        "--destination",
        type=IPv4Address,
        help="Specify the IP address of the routing destination.",
    )
    parser.add_argument(
        "-t",
        "--timepiece",
        action="store_true",
        help="Add temporal interfaces to query.",
    )
    parser.add_argument(
        "path",
        type=pathlib.Path,
        help="A snapshot directory to pass to pybatfish, or a JSON file obtained after reading such a directory.",
    )
    parser.add_argument(
        "-f",
        "--full-run",
        action="store_true",
        help="Also generate the .angler.json file if given a snapshot directory.",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="A location to save the output JSON to (defaults to [path].json or [path].angler.json)",
    )
    args = parser.parse_args()
    current_path: pathlib.Path = args.path
    if current_path.is_dir():
        bf = initialize_session(current_path, args.diagnostics)
        json_data = bast.json.query_session(bf)
        print("Completed Batfish JSON queries.")
        current_path = (
            Path(current_path.with_suffix(".json").name)
            if args.output is None
            else args.output
        )
        print(f"Saving result to {current_path}.")
        save_json(json_data, current_path)
        if not args.full_run:
            return
    # else:
    elif not args.full_run:
        with open(current_path) as fp:
            json_data = json.load(fp)
    else:
        raise Exception("--full-run option should be used with a directory.")
    # Add a query to an existing .angler.json file
    if ".angler" in current_path.suffixes:
        if not args.query:
            # if no query is provided, this will do nothing, so exit
            print("No query given for an existing .angler file. Exiting...")
            return
        a_ast = Program.from_dict(json_data)
        current_path = (
            current_path.with_stem(f"{current_path.stem}-{args.query}")
            if args.output is None
            else args.output
        )
    # Convert to an .angler.json file
    else:
        current_path = (
            current_path.with_stem(f"{current_path.stem}.angler")
            if args.output is None
            else args.output
        )
        bf_ast = bast.json.BatfishJson.from_dict(json_data)
        print("Successfully parsed Batfish AST!")
        a_ast = convert_batfish(bf_ast, simplify=args.simplify_bools)
    query = args.query
    if query:
        add_query(a_ast, query, args.destination, args.timepiece)
    save_json(a_ast, current_path)


if __name__ == "__main__":
    main()
