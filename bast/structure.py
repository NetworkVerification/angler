#!/usr/bin/env python3
"""
Structure definitions in the Batfish AST.
"""
from dataclasses import dataclass
from typing import Union
from serialize import Serialize, Serializable
import bast.base as ast
import bast.statement as stmt
import bast.communities as comms
import bast.btypes as types


@dataclass
class RoutingPolicy(
    ast.ASTNode,
    Serialize,
    policyname="name",
    statements=("statements", list[stmt.Statement]),
):
    policyname: str
    statements: list[stmt.Statement]


StructureValue = Union[ast.Vrf, ast.RouteFilter, RoutingPolicy, ast.Acl]


@dataclass
class StructureDef(ast.ASTNode, Serialize, value=("value", dict)):
    """
    A structure definition of some particular value, based on the
    StructureType of the enclosing Structure.
    TODO: perhaps we can flatten this?
    """

    value: StructureValue


class StructureType(ast.Variant):
    COMMS_MATCH = "Community_Set_Match_Expr"
    IP_ACCESS_LIST = "IP_Access_List"
    ROUTE_FILTER_LIST = "Route_Filter_List"
    ROUTE6_FILTER_LIST = "Route6_Filter_List"
    ROUTING_POLICY = "Routing_Policy"
    VRF = "VRF"

    def as_class(self) -> type:
        match self:
            case StructureType.COMMS_MATCH:
                return comms.CommunitySetMatchExpr
            case StructureType.IP_ACCESS_LIST:
                return ast.Acl
            case StructureType.ROUTE_FILTER_LIST:
                return list[ast.RouteFilter]
            case StructureType.ROUTE6_FILTER_LIST:
                # TODO
                return dict
            case StructureType.ROUTING_POLICY:
                return RoutingPolicy
            case StructureType.VRF:
                return ast.Vrf
            case _:
                raise ValueError(f"{self} is not a valid {self.__class__}")


@dataclass
class Structure(
    ast.ASTNode,
    Serialize,
    node=("Node", types.Node),
    ty=("Structure_Type", StructureType),
    struct_name=("Structure_Name", str),
    definition=("Structure_Definition", StructureDef),
):
    """
    A named structure in Batfish.
    """

    node: types.Node
    ty: StructureType
    struct_name: str
    definition: StructureDef

    def __post_init__(self):
        """
        Using the type of the structure, update the value of the underlying StructureDef
        to the appropriate type.
        """
        cls = self.ty.as_class()
        if isinstance(cls, Serializable):
            self.definition.value = cls.from_dict(self.definition.value)
