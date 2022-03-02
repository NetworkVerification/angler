#!/usr/bin/env python3
"""
Conversion tools to transform Batfish AST terms to Angler AST terms.
"""
from typing import Generic, Type, TypeVar
import bast.base as bast
import aast.base as aast

BT = TypeVar("BT", bound=bast.ASTNode)
AT = TypeVar("AT", bound=aast.ASTNode)


class ToAast(Generic[AT, BT]):
    """
    Class decorator to add a to_aast implementation to a given subclass
    of bast.base.ASTNode.
    to_aast converts this bast.base.ASTNode into an equivalent aast.base.ASTNode.
    """

    def __init__(self, ty: Type[AT] = None, **kwargs):
        self.ty = ty
        self.kwargs = kwargs

    def __call__(self, cls: Type[BT]) -> Type[BT]:

        _kwargs = self.kwargs
        ty = self.ty

        def to_aast(self: BT) -> AT:
            if ty is None:
                raise NotImplementedError()
            else:
                kwargs = {k: getattr(self, v) for k, v in _kwargs.items()}
                return ty(**kwargs)

        setattr(cls, to_aast.__name__, to_aast)
        return cls
