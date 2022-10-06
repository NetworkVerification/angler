#!/usr/bin/env python3
"""
Structure definitions in the Batfish AST.
"""
from dataclasses import dataclass
from serialize import Serialize, Field
from typing import cast
import bast.base as ast
import bast.statement as stmt
import bast.communities as comms
import bast.topology as topology
import bast.acl as acl
import bast.vrf as vrf


@dataclass
class RoutingPolicy(
    ast.ASTNode,
    Serialize,
    policyname="name",
    statements=Field("statements", list[stmt.Statement]),
):
    policyname: str
    statements: list[stmt.Statement]


@dataclass
class StructureDef(ast.ASTNode, Serialize, value=Field("value", dict)):
    """
    A structure definition of some particular value, based on the
    StructureType of the enclosing Structure.
    TODO: perhaps we can flatten this?
    """

    value: vrf.Vrf | acl.RouteFilterList | RoutingPolicy | acl.Acl | comms.CommunitySetMatchExpr


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
                return acl.Acl
            case StructureType.ROUTE_FILTER_LIST:
                return acl.RouteFilterList
            case StructureType.ROUTE6_FILTER_LIST:
                return acl.Route6FilterList
            case StructureType.ROUTING_POLICY:
                return RoutingPolicy
            case StructureType.VRF:
                return vrf.Vrf
            case _:
                raise ValueError(f"{self} is not a valid {self.__class__}")


@dataclass
class Structure(
    ast.ASTNode,
    Serialize,
    node=Field("Node", topology.Node),
    ty=Field("Structure_Type", StructureType),
    struct_name=Field("Structure_Name", str),
    definition=Field("Structure_Definition", StructureDef),
):
    """
    A named structure in Batfish.
    """

    node: topology.Node
    ty: StructureType
    struct_name: str
    definition: StructureDef

    def __post_init__(self):
        """
        Using the type of the structure, update the value of the underlying StructureDef
        to the appropriate type.
        """
        cls = self.ty.as_class()
        if issubclass(cls, Serialize) and isinstance(self.definition.value, dict):
            # special case: distinguish Community_Set_Match_Expr subclass
            if cls == comms.CommunitySetMatchExpr:
                cls = _infer_community_set_match_expr_class(self.definition.value)
            self.definition.value = cast(
                type(cls), cls.from_dict(self.definition.value)
            )


def _infer_community_set_match_expr_class(value):
    """
    As a hack, guess what the community set match expr should be
    based on the form of the given structure.
    We've seen only 2 kinds of expression: a single HasCommunity
    and (what we assume is) a CommunitySetMatchAll.
    The distinguishing feature between the two is whether the
    value contains an "expr" field (the former) or an "exprs" field
    (the latter).
    NOTE: This reasoning may not be sound if we ever encounter a case
    where the Batfish IR represents a CommunitySetMatchAny: we can't
    distinguish, based only on the "exprs" field, between ...Any and
    ...All.
    """
    if "expr" in value:
        return comms.HasCommunity
    elif "exprs" in value:
        return comms.CommunitySetMatchAll
    else:
        raise KeyError(f"Unable to infer CommunitySetMatchExpr subclass for {value}")
