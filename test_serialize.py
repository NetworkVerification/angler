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
class B(Serialize(c="c"), A):
    c: int


class E(Serialize(x="x")):
    def __init__(self, x):
        self.x = x


# pyright: reportMethodOrdering=false
class F(Serialize(x="x", y="y"), E):
    def __init__(self, x, y):
        self.x = x
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
    # try:
    b = B.from_dict(d)
    assert b.c == 2
    # except TypeError as e:
    #     assert str(e) == "B.__init__() missing 1 required positional argument: 'c'"


def test_from_dict_subclass_explicit():
    d = {"x": 0, "y": True}
    f = F.from_dict(d)
    assert f.x == d["x"] and f.y == d["y"]
