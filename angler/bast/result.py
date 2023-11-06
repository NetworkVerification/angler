#!/usr/bin/env python3
"""
Representation of Batfish's Result type.
Results distinguish how we chain together multiple policies.
See https://github.com/batfish/batfish/blob/master/projects/batfish-common-protocol/src/main/java/org/batfish/datamodel/routing_policy/Result.java
"""
from dataclasses import dataclass


@dataclass
class Result:
    _value: bool = False
    _exit: bool = False
    _fallthrough: bool = False
    _return: bool = False
