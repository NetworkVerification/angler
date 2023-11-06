#!/usr/bin/env python3
"""
The top-level JSON AST obtained from Batfish.
"""
from dataclasses import dataclass
from typing import Any
from angler.serialize import Serialize, Field
import angler.bast.base as base
import angler.bast.topology as topology
import angler.bast.structure as struct
import pybatfish.client.session as session
import pybatfish.datamodel.answer as answer
import angler.util


def collect_rows(answer: answer.TableAnswer) -> list[dict[str, Any]]:
    """
    Return the rows of the answers in the given TableAnswer.
    """
    return [row for a in answer["answerElements"] for row in a["rows"]]


def query_session(session: session.Session) -> dict[str, list[dict]]:
    topology = collect_rows(session.q.layer3Edges().answer())
    ips = collect_rows(session.q.ipOwners().answer())
    policy = collect_rows(session.q.nodeProperties().answer())
    # we need to set ignoreGenerated to False to get the auto-generated structures
    structures = collect_rows(session.q.namedStructures(ignoreGenerated=False).answer())
    # bgp_peers = collect_rows(session.q.bgpPeerConfiguration().answer())
    issues = collect_rows(session.q.initIssues().answer())
    # TODO: include static and connected routes
    # static_routes = collect_rows(session.q.routes(protocols="static").answer())
    # connected_routes = collect_rows(session.q.routes(protocols="connected").answer())
    return {
        "topology": topology,
        "ips": ips,
        "policy": policy,
        "declarations": structures,
        # "bgp": bgp_peers,
        "issues": issues,
    }


@dataclass
class BatfishJson(
    angler.util.ASTNode,
    Serialize,
    topology=Field("topology", list[topology.Edge]),
    ips=Field("ips", list[base.OwnedIP]),
    policy=Field("policy", list[dict]),
    # bgp=Field("bgp", list[base.BgpPeerConfig]),
    declarations=Field("declarations", list[struct.Structure]),
    issues=Field("issues", list[dict]),
):
    topology: list[topology.Edge]
    ips: list[base.OwnedIP]
    policy: list[dict]
    # bgp: list[base.BgpPeerConfig]
    declarations: list[struct.Structure]
    issues: list[dict]

    @staticmethod
    def from_session(session: session.Session) -> "BatfishJson":
        return BatfishJson.from_dict(query_session(session))
