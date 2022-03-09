from dataclasses import dataclass
from serialize import Serialize, Field
from aast.base import Variant, ASTNode
import aast.expression as expr


class StatementType(Variant):
    IF = "If"
    ASSIGN = "Assign"
    RETURN = "Return"

    def as_class(self) -> type:
        match self:
            case StatementType.IF:
                return IfStatement
            case StatementType.ASSIGN:
                return AssignStatement
            case StatementType.RETURN:
                return ReturnStatement
            case _:
                raise NotImplementedError(f"{self} conversion not implemented.")


@dataclass
class Statement(
    ASTNode,
    Serialize,
    with_type="$type",
    delegate=("$type", StatementType.parse_class),
):
    """
    The base class for statements.
    """

    ...


@dataclass
class IfStatement(
    Statement,
    Serialize,
    with_type="$type",
    guard=Field("guard", expr.Expression[bool]),
    true_stmts=Field("trueStatements", list[Statement], []),
    false_stmts=Field("falseStatements", list[Statement], []),
    comment="comment",
):
    """
    An if statement allowing branching control flow.
    The true and false statements can be left empty.
    """

    guard: expr.Expression[bool]
    true_stmts: list[Statement]
    false_stmts: list[Statement]
    comment: str


@dataclass
class AssignStatement(
    Statement,
    Serialize,
    with_type="$type",
    lhs=Field("lhs", expr.Var),
    rhs=Field("rhs", expr.Expression),
):
    lhs: expr.Var
    rhs: expr.Expression


@dataclass
class ReturnStatement(
    Statement,
    Serialize,
    with_type="$type",
    return_value=Field("return_value", expr.Expression),
):
    return_value: expr.Expression
