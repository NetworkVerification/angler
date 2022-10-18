#!/usr/bin/env python3
"""
VRFs in the Batfish AST.
"""
from typing import Optional
from ipaddress import IPv4Address
from dataclasses import dataclass
from serialize import Serialize, Field
import bast.base as ast


@dataclass
class Ipv4UnicastAddressFamily(
    ast.ASTNode, Serialize, export_policy="exportPolicy", import_policy="importPolicy"
):
    export_policy: Optional[str]
    import_policy: Optional[str]


@dataclass
class BgpActivePeerConfig(
    ast.ASTNode,
    Serialize,
    default_metric=Field("defaultMetric", int),
    address_family=Field("ipv4UnicastAddressFamily", Ipv4UnicastAddressFamily),
    local_as=Field("localAs", int),
    local_ip=Field("localIp", IPv4Address),
    remote_as=Field("remoteAsns", int),
    peer_ip=Field("peerAddress", IPv4Address),
    # TODO: other fields?
):
    """
    https://github.com/batfish/batfish/blob/master/projects/batfish-common-protocol/src/main/java/org/batfish/datamodel/BgpActivePeerConfig.java
    A BGP config to allow peering with a single remote peer.
    """

    default_metric: int
    address_family: Ipv4UnicastAddressFamily
    local_as: int
    local_ip: IPv4Address
    # NOTE: this is sometimes the empty string
    remote_as: int
    peer_ip: IPv4Address


@dataclass
class BgpProcess(
    ast.ASTNode,
    Serialize,
    neighbors=Field("neighbors", dict[IPv4Address, BgpActivePeerConfig]),
    router=Field("routerId", IPv4Address),
):
    neighbors: dict[IPv4Address, BgpActivePeerConfig]
    router: IPv4Address


@dataclass
class OspfProcess(
    ast.ASTNode,
    Serialize,
    admin_costs="adminCosts",
    areas="areas",
    # TODO: other fields?
):
    admin_costs: dict
    areas: dict


@dataclass
class Vrf(
    ast.ASTNode,
    Serialize,
    vrfname="name",
    bgp=Field("bgpProcess", BgpProcess, None),
    ospf=Field("ospfProcesses", dict[str, OspfProcess], None),
    resolution="resolutionPolicy",
):
    vrfname: str
    resolution: str
    bgp: Optional[BgpProcess] = None
    ospf: Optional[dict] = None
