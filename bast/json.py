#!/usr/bin/env python3
"""
The top-level JSON AST obtained from Batfish.
"""
from dataclasses import dataclass
from typing import Any
from serialize import Serialize
import bast.base as ast
import bast.btypes as types
import bast.structure as struct
import pybatfish.client.session as session
import pybatfish.datamodel.answer as answer


def collect_rows(answer: answer.TableAnswer) -> list[dict[str, Any]]:
    """
    Return the rows of the answers in the given TableAnswer.
    """
    return [row for a in answer["answerElements"] for row in a["rows"]]


def query_session(session: session.Session) -> dict:
    topology = session.q.layer3Edges().answer()
    policy = session.q.nodeProperties().answer()
    structures = session.q.namedStructures().answer()
    return {
        "topology": topology,
        "policy": policy,
        "declarations": structures,
    }


@dataclass
class BatfishJson(
    ast.ASTNode,
    Serialize,
    topology=("topology", list[types.Edge]),
    policy="policy",
    declarations=("declarations", list[struct.Structure]),
):
    topology: list[types.Edge]
    policy: dict
    declarations: list[struct.Structure]

    @staticmethod
    def from_session(session: session.Session) -> "BatfishJson":
        return BatfishJson.from_dict(query_session(session))
