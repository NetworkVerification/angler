#!/usr/bin/env python3
"""
Utilities for manipulating ASTs.
"""
from enum import Enum
from typing import Callable
from dataclasses import dataclass, fields, is_dataclass
from collections.abc import Iterable
from angler.serialize import Serialize


def parse_qualified_class(name: str) -> str:
    """
    Given a string representing a namespaced class, return the class name.
    Has the following behavior depending on the form of name, mimicking Batfish:
    - Qualified class name: "namespaces.name" -> "name"
    - Qualified class name with named subclass: "namespaces.class$name" -> "name"
    - Unqualified name: "name" -> "name"
    Has the following behavior mimicking Angler:
    - Class name with inner types: "name(inner_name;...)" -> "name"
    """
    try:
        _, name = name.rsplit(sep=".", maxsplit=1)
        # if a $ is found, name will contain the string following it
        # if $ is not found, name will contain the original string
        name = name[name.rfind("$") + 1 :]
    finally:
        # drop anything that follows an open parenthesis
        front_index = name.find("(")
        return name if front_index == -1 else name[:front_index]


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
        Qualified names (names which include Java-like dot-notation to indicate namespaces)
        are parsed according to `parse_qualified_class`.
        """
        return cls(parse_qualified_class(s)).as_class()


@dataclass
class ASTNode(Serialize):
    """The base class for AST nodes."""

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
