#!/usr/bin/env python3
from serialize import Serialize
from dataclasses import dataclass


@dataclass
class Point3D(Serialize(coords=("coords", tuple[int, int, int]))):
    coords: tuple[int, int, int]


@dataclass
class A(Serialize()):
    ...


@dataclass
class B(A, Serialize(c="c")):
    c: int


def test_empty_fields():
    a = A.from_dict({})
    assert a == A()


def test_skip_field():
    d = {"c": 2}
    a = A.from_dict(d)
    assert a == A()


def test_from_dict_tuple():
    coords = (0, 0, 1)
    p = Point3D.from_dict({"coords": coords})
    assert p.coords == coords


def test_from_dict_subclass():
    d = {"c": 2}
    b = B.from_dict(d)
    # FIXME: does B's argument get consumed?
    assert b.c == d["c"]
