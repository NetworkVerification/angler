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
        "-a",
        "--no-merge-asns",
        action="store_false",
        help="Treat every external IP as a separate external neighbor, even if two external IPs share an AS number.",
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
        save_json(json_data, out_path)
    else:
        with open(args.path) as fp:
            json_data = json.load(fp)
        if ".angler" in args.path.suffixes:
            if not args.query:
                # if no query is provided, this will do nothing, so exit
                print("No query given for an existing .angler file. Exiting...")
                return
            a_ast = Program.from_dict(json_data)
            out_path = (
                args.path.with_stem(f"{args.path.stem}-{args.query}")
                if args.output is None
                else args.output
            )
        else:
            out_path = (
                args.path.with_stem(f"{args.path.stem}.angler")
                if args.output is None
                else args.output
            )
            bf_ast = bast.json.BatfishJson.from_dict(json_data)
            print("Successfully parsed Batfish AST!")
            a_ast = convert_batfish(
                bf_ast, simplify=args.simplify_bools, merge_asns=args.no_merge_asns
            )
        query = args.query
        if query:
            add_query(a_ast, query, args.destination, args.timepiece)
        save_json(a_ast, out_path)


if __name__ == "__main__":
    main()
