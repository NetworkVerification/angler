#!/usr/bin/env python3
from serialize import *
from dataclasses import dataclass
import pytest


@dataclass
class Point3D(Serialize, coords=Field("coords", tuple[int, int, int])):
    coords: tuple[int, int, int]


@dataclass
class A(Serialize):
    ...


@dataclass
class B(A, Serialize, c=Field("c")):
    c: int


class E(Serialize, x=Field("x")):
    def __init__(self, x):
        self.x = x


class F(E, Serialize, x=Field("x"), y=Field("y")):
    def __init__(self, x, y, z=5):
        self.x = x
        self.y = y
        self.z = z


class G(E, Serialize, x=Field("x", int, 0)):
    def __init__(self, x=1):
        self.x = x


class H(E, Serialize, x=Field("x", int, 0)):
    def __init__(self):
        self.x = 2


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


def test_from_dict_subclass_dataclass():
    d = {"c": 2}
    b = B.from_dict(d)
    assert b.c == 2


def test_from_dict_subclass_explicit():
    d = {"x": 0, "y": True}
    f = F.from_dict(d)
    assert f.x == d["x"] and f.y == d["y"] and f.z == 5


def test_default_field():
    d = {}
    g = G.from_dict(d)
    assert g.x == G.fields["x"].default


@pytest.mark.xfail(raises=TypeError, strict=True)
def test_default_field_ignored():
    d = {}
    H.from_dict(d)
