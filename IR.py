from enum import Enum
from typing import Any, Callable, Optional, Union
from serialize import Serializable, Serialize
from ipaddress import IPv4Address, IPv4Network, IPv4Interface
from dataclasses import dataclass
from collections.abc import Iterable
from bat_ast import Action

class Community:
    def __init__(self, comm_str):
        self.comm_str = comm_str
        sep_pos = comm_str.find(':')
        if sep_pos == -1:
            raise ValueError("Invalid community string")
        self.ASN = comm_str[:sep_pos]
        self.tag = comm_str[sep_pos+1:]

class ExpressionType(Enum):
    ''' Type of expression '''

    VAR  = "Variable"
    MATCH = "Match"
    # add, subtract
    SETUNION = "SetUnion"
    SETDIFFERENCE = "SetDifference"
    SETCONTAINMENT = "SetContainment"
    PREPEND = "Prepend" # add to front of list
    # value types (literals)
    TRUE = "True"
    FALSE = "False"
    INT = "Int"
    LIST = "List"
    SET = "Set"
    IPADDRESS = "IPaddress" # string e.g. 10.0.1.0
    IPPREFIX = "IPprefix" # tuple (ipaddress, prefix width)
    COMMUNITY = "Community" # tuple (AS number, tag) TODO: confirm

    def enum_class(self) -> type:
        match self:
            case ExpressionType.VAR:
                return Var
            case ExpressionType.MATCH:
                return Match
            case ExpressionType.SETUNION:
                return SetUnion
            case ExpressionType.SETDIFFERENCE:
                return SetDifference
            case ExpressionType.INT:
                return LiteralInt
            case ExpressionType.LIST:
                return LiteralList
            case ExpressionType.SET:
                return LiteralSet
            case ExpressionType.IPADDRESS:
                return IPv4Address
            case ExpressionType.IPPREFIX:
                return IPv4Network
            case ExpressionType.COMMUNITY:
                return Community
            case _:
                raise NotImplementedError()

class StatementType(Enum):
    IF = "If"
    ASSIGN = "Assign"
    RETURN = "Return"

    def enum_class(self) -> type:
        match self:
            case StatementType.IF:
                return IfStatement
            case StatementType.ASSIGN:
                return AssignStatement
            
            

@dataclass
class ASTNode(Serialize):
    def visit(self, f: Callable) -> None:
        f(self)
        for field in self.fields:
            if isinstance(field, Iterable):
                for ff in field:
                    if isinstance(ff, ASTNode):
                        ff.visit(f)
            else:
                field.visit(f)



@dataclass
class Expression(
    ASTNode,
    Serialize,
    delegate=("class", lambda s: ExpressionType(s).enum_class()),
):
    """
    The base class for expressions.
    """

    ...


@dataclass
class Statement(
    ASTNode,
    Serialize,
    delegate=(
        "class",
        lambda s: StatementType(s).enum_class(),
    ),
):
    """
    The base class for statements.
    """

    ...

# values

@dataclass
class LiteralInt(Expression, Serialize, value=("value", int)):
    value: int

@dataclass
class LiteralList(Expression, Serialize, elements=("list", list[Expression])):
    list: list[Expression]

@dataclass
class LiteralSet(Expression, Serialize, elements=("set", set[Expression])):
    set: set[Expression]


@dataclass
class Var(Expression, Serialize, name=("name", str)):
    ''' A class representing a variable'''
    name: str



# @dataclass
# class DestinationNetwork(Var):
#     ...


# @dataclass
# class InputCommunities(Var):
#     ...

# @dataclass
# class LocalPreference(Var):
#     ...

# @dataclass
# class Metric(Var):
#     ...


@dataclass
class Contains(Expression, Serialize, iterable="iterable", element="element"):
    # Does iterable contain element?
    iterable: Expression
    element: Expression # typically a literal

@dataclass
class SetUnion(Expression, Serialize, exprs=("exprs", list[Expression])):
    exprs: list[Expression]


@dataclass
class SetDifference(
    Expression,
    Serialize,
    initial=("initial", Expression),
    remove=("removalCriterion", Expression),
):
    initial: Expression
    remove: Expression

@dataclass
class Match(
    Expression, 
    Serialize, 
    match_var = ("match_var", Var),
    match_list = ("match_list", Expression)):
        match_var: Var # variable to match on
        match_list: Expression # list of permit / deny rules 


@dataclass
class AssignStatement(
    Statement,
    Serialize,
    lhs=("lhs", Var),
    rhs=("rhs", Expression)
):
    lhs: Var
    rhs: Expression

@dataclass
class IfStatement(
    Statement,
    Serialize,
    guard=("guard", Expression),
    true_stmts=("trueStatements", list[Statement]),
    false_stmts=("falseStatements", list[Statement]),
    comment="comment",
):
    guard: Expression
    true_stmts: list[Statement]
    false_stmts: list[Statement]
    comment: str



    