#!/usr/bin/env python3
"""
Topology information in the Batfish AST.
"""
import igraph
from dataclasses import dataclass
from serialize import Serialize, Field
from ipaddress import IPv4Address


@dataclass
class Node(Serialize, nodeid="id", nodename="name"):
    """A node in the network."""

    nodeid: str
    nodename: str


@dataclass
class Interface(Serialize, host="hostname", iface="interface"):
    host: str
    iface: str


@dataclass
class Edge(
    Serialize,
    iface=Field("Interface", Interface),
    ips=Field("IPs", list[IPv4Address]),
    remote_iface=Field("Remote_Interface", Interface),
    remote_ips=Field("Remote_IPs", list[IPv4Address]),
):
    """
    A representation of a directed edge between two interfaces.
    The first (non-remote) interface is the source.
    The second remote interface is the target.
    """

    iface: Interface
    ips: list[IPv4Address]
    remote_iface: Interface
    remote_ips: list[IPv4Address]


# TODO: unused -- remove?
def edges_to_graph(edges: list[Edge]) -> igraph.Graph:
    """
    Return a directed graph constructed from a list of Edges.
    Each vertex has an associated name (the hostname),
    and each edge has a list of IP addresses associated with its endpoints.
    """
    hosts = dict()
    edge_ips = []
    i = 0
    igraph_edges = []
    for edge in edges:
        src = edge.iface.host
        snk = edge.remote_iface.host
        if src not in hosts:
            hosts[src] = i
            i += 1
        if snk not in hosts:
            hosts[snk] = i
            i += 1
        igraph_edges.append((hosts[src], hosts[snk]))
        edge_ips.append((edge.ips, edge.remote_ips))
    # sort the hosts by the index and then return the host names in order
    host_names = [h for h, _ in sorted(hosts.items(), key=lambda x: x[1])]
    return igraph.Graph(
        edges=igraph_edges,
        directed=True,
        vertex_attrs={"name": host_names},
        edge_attrs={"ips": edge_ips},
    )
