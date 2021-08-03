"""
IPython-specific widgets
"""
# Copyright (c) 2021 trike contributors.
# Distributed under the terms of the Modified BSD License.

from .describe_tool import DescribeTool
from .rdf_loader import RDFLoader, from_rdf
from .turtle_magic import turtle

__all__ = [
    "turtle",
    "RDFGraphWidget",
    "DescribeTool",
    "RDFLoader",
    "from_rdf",
]
