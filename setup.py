# Copyright (c) 2021 ipyrdf contributors.
# Distributed under the terms of the Modified BSD License.

import re
from pathlib import Path

import setuptools

NAME = "ipyrdf"

__version__ = re.findall(
    r'__version__ = "([^"]+)"',
    (Path(__file__).parent / NAME / "_version.py").read_text(),
)[0]

if __name__ == "__main__":
    setuptools.setup(
        version=__version__,
    )
