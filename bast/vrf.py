#!/usr/bin/env python3
"""
VRFs in the Batfish AST.
"""
from typing import Optional
from ipaddress import IPv4Address, IPv4Interface
from dataclasses import dataclass
from serialize import Serialize, Field
import bast.base as ast


@dataclass
class BgpActivePeerConfig(
    ast.ASTNode,
    Serialize,
    default_metric=Field("defaultMetric", int),
    local_as=Field("localAs", int),
    local_ip=Field("localIp", IPv4Address),
    remote_as=Field("remoteAsns", int),
    peer_ip=Field("peerAddress", IPv4Address),
):
    default_metric: int
    local_as: int
    local_ip: IPv4Address
    remote_as: int
    peer_ip: IPv4Address


@dataclass
class BgpProcess(
    ast.ASTNode,
    Serialize,
    neighbors=Field("neighbors", dict[IPv4Interface, BgpActivePeerConfig]),
    router=Field("routerId", IPv4Address),
):
    neighbors: dict[IPv4Interface, BgpActivePeerConfig]
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
