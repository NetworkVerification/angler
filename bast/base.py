#!/usr/bin/env python3
"""
Base utilities for parsing the Batfish AST.
"""
from enum import Enum
from typing import Callable
from ipaddress import IPv4Address
from dataclasses import dataclass, fields, is_dataclass
from serialize import Serialize, Field
from collections.abc import Iterable
import bast.topology as topology


def parse_bf_clsname(name: str) -> str:
    """
    Given a string representing a class in batfish's namespace,
    return the class name.
    Has the following behavior depending on the form of name:
    - Qualified class name: "namespaces.name" -> "name"
    - Qualified class name with named subclass: "namespaces.class$name" -> "name"
    - Unqualified name: "name" -> "name"
    """
    try:
        _, name = name.rsplit(sep=".", maxsplit=1)
        # if a $ is found, name will contain the string following it
        # if $ is not found, name will contain the original string
        return name[name.rindex("$") + 1 :]
    except ValueError:
        return name


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
        return cls(parse_bf_clsname(s)).as_class()


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
    ASTNode,
    Serialize,
    node=Field("Node", topology.Node),
    local_as=Field("Local_AS", int),
    local_ip=Field("Local_IP", IPv4Address),
    remote_as=Field("Remote_AS", int),
    remote_ip=Field("Remote_IP", RemoteIpAddress),
    import_policy=Field("Import_Policy", list[str]),
    export_policy=Field("Export_Policy", list[str]),
):
    node: topology.Node
    local_as: int
    local_ip: IPv4Address
    remote_as: int
    remote_ip: RemoteIpAddress
    import_policy: list[str]
    export_policy: list[str]
