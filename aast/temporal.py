#!/usr/bin/env python3
# Representation of temporal predicates in Angler AST.
from dataclasses import dataclass, field
from util import Variant
from serialize import Field, Serialize


class TemporalOpType(Variant):
    FINALLY = "Finally"
    GLOBALLY = "Globally"
    UNTIL = "Until"

    def as_class(self) -> type:
        match self:
            case TemporalOpType.FINALLY:
                return Finally
            case TemporalOpType.GLOBALLY:
                return Globally
            case TemporalOpType.UNTIL:
                return Until
            case _:
                raise NotImplementedError(f"{self} conversion not implemented.")


@dataclass
class TemporalOp(
    Serialize,
    delegate=("$type", TemporalOpType.parse_class),
):
    ...


@dataclass
class Finally(
    TemporalOp, Serialize, time="time", then="then", ty=Field("$type", str, "Finally")
):
    time: int
    then: str
    ty: str = field(default="Finally", init=False)


@dataclass
class Until(
    TemporalOp,
    Serialize,
    time="time",
    before="before",
    after="after",
    ty=Field("$type", str, "Until"),
):
    time: int
    before: str
    after: str
    ty: str = field(default="Until", init=False)


@dataclass
class Globally(TemporalOp, Serialize, p="p", ty=Field("$type", str, "Globally")):
    p: str
    ty: str = field(default="Globally", init=False)
