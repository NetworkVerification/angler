#!/usr/bin/env python3
"""
Base angler.utilities for parsing the Batfish AST.
"""
from enum import Enum
from ipaddress import IPv4Address
from dataclasses import dataclass
from angler.serialize import Serialize, Field
import angler.bast.topology as topology
import angler.util


class RemoteIpType(Enum):
    IP = "Ip"


@dataclass
class RemoteIpAddress(
    Serialize, value=Field("value", IPv4Address), schema=Field("schema", RemoteIpType)
):
    schema: RemoteIpType
    value: IPv4Address


@dataclass
class BgpPeerConfig(
    angler.util.ASTNode,
    Serialize,
    desc=Field("Description", str),
    node=Field("Node", topology.Node),
    local_as=Field("Local_AS", int),
    local_ip=Field("Local_IP", IPv4Address),
    remote_as=Field("Remote_AS", int),
    remote_ip=Field("Remote_IP", RemoteIpAddress),
    import_policy=Field("Import_Policy", list[str]),
    export_policy=Field("Export_Policy", list[str]),
):
    desc: str
    node: topology.Node
    local_as: int
    local_ip: IPv4Address
    remote_as: int
    remote_ip: RemoteIpAddress
    import_policy: list[str]
    export_policy: list[str]


@dataclass
class OwnedIP(
    angler.util.ASTNode,
    Serialize,
    active=Field("Active", bool),
    ip=Field("IP", IPv4Address),
    interface=Field("Interface", str),
    mask=Field("Mask", int),
    node=Field("Node", topology.Node),
):
    """Representation of a row returned by the ipOwners() query."""

    active: bool
    ip: IPv4Address
    interface: str
    mask: int
    node: topology.Node
