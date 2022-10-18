#!/usr/bin/env python3
"""
Base utilities
"""
from enum import Enum
from typing import Callable
from ipaddress import IPv4Address
from dataclasses import dataclass, fields, is_dataclass
from serialize import Serialize, Field
from collections.abc import Iterable
import bast.topology as topology


class Variant(Enum):
    """
    A wrapper around the standard Python enum which we use for specifying varieties of
    terms, e.g. the different types of boolean expression.
    Each element of a Variant has an associated type accessed using `as_class`.
    """

    def as_class(self) -> type:
        """
        Return a type associated with each element of the enum.
        """
        raise NotImplementedError(
            f"Variant {self.__class__} must implement 'as_class'."
        )

    @classmethod
    def parse_class(cls, s: str) -> type:
        """
        Return the type associated with a given string parsed into this variant.
        """
        return cls(s).as_class()


@dataclass
class ASTNode(Serialize):
    def visit(self, f: Callable) -> None:
        # recursively descend through the fields of the ASTNodes
        if is_dataclass(self):
            f(self)
            for field in fields(self):
                field_node = getattr(self, field.name)
                if isinstance(field_node, dict):
                    for field_elem in [
                        e for e in field_node.values() if isinstance(e, ASTNode)
                    ]:
                        field_elem.visit(f)
                elif isinstance(field_node, Iterable):
                    for field_elem in [e for e in field_node if isinstance(e, ASTNode)]:
                        field_elem.visit(f)
                elif isinstance(field_node, ASTNode):
                    field_node.visit(f)


class RemoteIpType(Variant):
    IP = "Ip"

    def as_class(self) -> type:
        match self:
            case RemoteIpType.IP:
                return RemoteIpAddress
            case _:
                raise NotImplementedError(f"{self} conversion not implemented.")

    @classmethod
    def parse_class(cls, s: str) -> type:
        """
        Return the type associated with a given string parsed into this variant.
        """
        return cls(s).as_class()


@dataclass
class RemoteIp(Serialize, delegate=("schema", RemoteIpType.parse_class)):
    ...


@dataclass
class RemoteIpAddress(Serialize, value=Field("value", IPv4Address)):
    value: IPv4Address


@dataclass
class BgpPeerConfig(
    ASTNode,
    Serialize,
    node=Field("Node", topology.Node),
    local_as=Field("Local_AS", int),
    local_ip=Field("Local_IP", IPv4Address),
    remote_as=Field("Remote_AS", int),
    remote_ip=Field("Remote_IP", RemoteIp),
    import_policy=Field("Import_Policy", str),
    export_policy=Field("Export_Policy", str),
):
    node: str
    local_as: int
    local_ip: IPv4Address
    remote_as: int
    remote_ip: RemoteIp
    import_policy: str
    export_policy: str
