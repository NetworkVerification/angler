#!/usr/bin/env python3
# Export Batfish JSON snapshots
#
import json
import sys
from pybatfish.client.session import Session
from pybatfish.datamodel import *
from pybatfish.datamodel.answer import *
from pybatfish.datamodel.flow import *
from pandas.io.json import to_json


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


def get_node_properties(session: Session):
    """
    Return the properties of the network nodes.
    """
    return session.q.nodeProperties().answer()


def get_layer3_edges(session: Session):
    """
    Return the layer 3 edges of the network.
    """
    return session.q.layer3Edges().answer()


def get_named_structures(session: Session):
    """
    Return the named structures of the network.
    """
    return session.q.namedStructures().answer()


if __name__ == "__main__":
    bf = initialize_session(sys.argv[1])
    info = {
        "topology": get_layer3_edges,
        "policy": get_node_properties,
        "declarations": get_named_structures,
    }
    output = json.dumps({k: v(bf) for k, v in info.items()})
    print(output)
