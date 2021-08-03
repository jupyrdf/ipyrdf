"""
IPython-specific widgets
"""
# Copyright (c) 2021 trike contributors.
# Distributed under the terms of the Modified BSD License.

from .sparql_magic import sparql
from .widget_sparql import SparqlWidget

__all__ = [
    "SparqlWidget",
    "sparql",
]
