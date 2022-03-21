#!/usr/bin/env python3
# Representation of temporal predicates in Angler AST.
from dataclasses import dataclass
from aast.base import Variant
from serialize import Serialize


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
class Finally(TemporalOp, Serialize, time="time", then="then"):
    time: int
    then: str


@dataclass
class Until(TemporalOp, Serialize, time="time", before="before", after="after"):
    time: int
    before: str
    after: str


@dataclass
class Globally(TemporalOp, Serialize, p="p"):
    p: str
