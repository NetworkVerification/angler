#!/usr/bin/env python3
"""
The top-level representation of a network in Angler.
"""

from dataclasses import dataclass, field, replace
from ipaddress import IPv4Address, IPv4Network
from typing import Optional, Self
from collections.abc import Iterable
import igraph
import angler.aast.statement as stmt
import angler.aast.types as ty

from angler.serialize import Field, Serialize


@dataclass
class Func(Serialize, arg="arg", body=Field("body", list[stmt.Statement])):
    """
    A function from T to T taking a single argument "arg" of type T
    and executing the statements of its body.
    """

    arg: str
    body: list[stmt.Statement]


@dataclass(order=True)
class Policies(Serialize, asn=Field("Asn", int), imp="Import", exp="Export"):
    """
    Representation of a node in the network with a particular defined import and export policy.
    May optionally specify an AS number if on an inter-network connection.
    """

    asn: Optional[int]
    imp: Optional[str]
    exp: Optional[str]


@dataclass(frozen=True, order=True)
class ExternalPeer(
    Serialize,
    ip=Field("Ip", IPv4Address),
    asnum=Field("ASNumber", int, None),
    peering=Field("Peering", list[str], []),
):
    """
    Representation of an external peer connection.
    """

    ip: IPv4Address
    asnum: Optional[int] = None
    peering: list[str] = field(default_factory=list)


@dataclass
class Properties(
    Serialize,
    asnum=Field("ASNumber", int, None),
    prefixes=Field("Prefixes", set[IPv4Network]),
    policies=Field("Policies", dict[str, Policies]),
    declarations=Field("Declarations", dict[str, Func]),
):
    """
    Representation of the properties of a particular router in the network,
    including its AS number, its prefixes, the policies it applies for its
    peer sessions, and function declarations.
    """

    asnum: Optional[int] = None
    prefixes: set[IPv4Network] = field(default_factory=set)
    policies: dict[str, Policies] = field(default_factory=dict)
    declarations: dict[str, Func] = field(default_factory=dict)

    def add_prefix_from_ip(self, ip: IPv4Address):
        """
        Add a /24 prefix to the properties based on the given address.
        """
        # strict=False causes this to mask the last 8 bits
        net = IPv4Network((ip, 24), strict=False)
        self.prefixes.add(net)


@dataclass
class Network(
    Serialize,
    route=Field("Route", dict[str, ty.TypeAnnotation]),
    nodes=Field("Nodes", dict[str, Properties]),
    externals=Field("Externals", list[ExternalPeer]),
):
    """
    A representation of a network in Angler's AST.
    """

    route: dict[str, ty.TypeAnnotation]
    nodes: dict[str, Properties]
    # External peers and the nodes they connect to
    externals: list[ExternalPeer]

    def to_graph(self) -> igraph.Graph:
        """
        Return an (undirected) graph representing the given network.
        All nodes in the graph have names as follows:
        - (Internal) nodes' names are the given keys.
        - External peers' node names are a string representation of their IP.
        """
        all_nodes = set()
        all_edges = list()
        for node, properties in self.nodes.items():
            all_nodes.add(node)
            for neighbor in properties.policies.keys():
                all_nodes.add(neighbor)
                all_edges.append((neighbor, node))
        for ext in self.externals:
            node = str(ext.ip)
            all_nodes.add(node)
            for neighbor in ext.peering:
                all_nodes.add(neighbor)
                all_edges.append((neighbor, node))
        g = igraph.Graph()
        g.add_vertices(n for n in all_nodes)
        g.add_edges(all_edges)
        return g

    def subnet(self, nodes: list[str]) -> Self:
        """
        Return a new `Network` instance restricted to only the nodes
        in the given list `nodes`.
        """
        new_nodes = {
            n: replace(
                prop,
                # drop edges for removed neighbors
                policies={k: v for k, v in prop.policies.items() if k in nodes},
            )
            for n, prop in self.nodes.items()
            # drop removed nodes
            if n in nodes
        }
        new_externals = [
            replace(e, peering=[p for p in e.peering if p in nodes])
            for e in self.externals
            # drop removed nodes
            if str(e.ip) in nodes
        ]
        new = replace(self, nodes=new_nodes, externals=new_externals)
        return new

    def scaling_subnets(self, nodes: list[str]) -> Iterable[Self]:
        """
        Yield subnets of the network for each successive subsequence of `nodes`.
        """
        g = self.to_graph()
        node_indices = [v.index for v in g.vs.select(name_in=nodes)]
        for subnet_nodes in _scaling_subgraphs(g, node_indices):
            node_names = [g.vs[n]["name"] for n in subnet_nodes]
            yield self.subnet(node_names)


def _scaling_subgraphs(g: igraph.Graph, nodes: list[int]) -> Iterable[list[int]]:
    """
    Yield lists of nodes in the subgraphs of the given list of `nodes`.
    Each list contains all the nodes that are neighbors of the sublist in `g`,
    excluding any nodes that are themselves present in the given list.
    The total number of lists yielded is `len(nodes) - 2`: the first list
    contains only 1 node from `nodes`,
    and the last list contains `len(nodes) - 1` nodes from `nodes`.

    >>> g = igraph.Graph()
    >>> g.add_vertices(5)
    >>> g.add_edges([(0, 1), (1, 2), (0, 3), (1, 4)])
    >>> [nodes for nodes in scaling_subgraphs(g, [0, 1, 2])]
    [[0, 3], [0, 1, 3, 4]]
    """
    # go between 1 and len(nodes) since we don't want an empty graph and we don't want the original
    for i in range(1, len(nodes)):
        subnet_nodes = nodes[:i]
        # neighborhood() returns the node itself and all adjacent neighbors
        subnet_neighbors = set(n for nbrs in g.neighborhood(subnet_nodes) for n in nbrs)
        # remove any neighbors that are being excluded
        subnet_neighbors.difference_update(nodes[i:])
        yield list(subnet_neighbors)
