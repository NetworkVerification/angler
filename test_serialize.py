#!/usr/bin/env python3
from serialize import Serialize, Serialize2
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


@Serialize2(x="x")
class E:
    def __init__(self, x):
        super().__init__()
        self.x = x


@Serialize2(x="x", y="y")
class F(E):
    def __init__(self, x, y):
        super().__init__(x)
        self.y = y


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
    # FIXME: does B's argument get consumed?
    assert b.c == d["c"]


def test_from_dict_subclass_explicit():
    d = {"x": 0, "y": True}
    f = F.from_dict(d)
    assert f.x == d["x"] and f.y == d["y"]
