#!/usr/bin/env python3
"""
Conversion tools to transform Batfish AST terms to Angler AST terms.
"""
import bast.base as bast
import aast.base as aast


class ToAast:
    """
    Class decorator to add a to_aast implementation.
    """

    def __init__(self, cls):
        self._cls = cls

    def __call__(self, ty: type = None, **kwargs):
        kwargs = {k: getattr(self._cls, v) for k, v in kwargs.items()}

        def to_aast(self):
            if ty is None:
                raise NotImplementedError()
            else:
                return ty(**kwargs)

        self._cls.to_aast = to_aast
        return self._cls
