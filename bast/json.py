#!/usr/bin/env python3
"""
The top-level JSON AST obtained from Batfish.
"""
from dataclasses import dataclass
from typing import Any
from serialize import Serialize, Field
import bast.base as ast
import bast.topology as topology
import bast.structure as struct
import pybatfish.client.session as session
import pybatfish.datamodel.answer as answer


def collect_rows(answer: answer.TableAnswer) -> list[dict[str, Any]]:
    """
    Return the rows of the answers in the given TableAnswer.
    """
    return [row for a in answer["answerElements"] for row in a["rows"]]


def query_session(session: session.Session) -> dict[str, list[dict]]:
    topology = collect_rows(session.q.layer3Edges().answer())
    policy = collect_rows(session.q.nodeProperties().answer())
    structures = collect_rows(session.q.namedStructures().answer())
    return {
        "topology": topology,
        "policy": policy,
        "declarations": structures,
    }


@dataclass
class BatfishJson(
    ast.ASTNode,
    Serialize,
    topology=Field("topology", list[topology.Edge]),
    policy=Field("policy", list[dict]),
    declarations=Field("declarations", list[struct.Structure]),
):
    topology: list[topology.Edge]
    policy: list[dict]
    declarations: list[struct.Structure]

    @staticmethod
    def from_session(session: session.Session) -> "BatfishJson":
        return BatfishJson.from_dict(query_session(session))
