#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Setup for dbml-to-sqlalchemy
"""

import os
from setuptools import setup, find_packages

__version_info__ = (0, 9, 1)
VERSION = '.'.join([str(val) for val in __version_info__])
NAME = "dbml-to-sqlalchemy"
DESC = "dbml-to-sqlalchemy extension for sqlachemy: upload dbml model in orm sqlalchemy"
URLPKG = "https://github.com/fraoustin/dbml-to-sqlalchemy.git"

HERE = os.path.abspath(os.path.dirname(__file__))

# README AND CHANGES
with open(os.path.join(HERE, 'README.md')) as readme:
    with open(os.path.join(HERE, 'CHANGES.md')) as changelog:
        LONG_DESC = readme.read() + '\n\n' + changelog.read()
# REQUIREMENTS
with open('REQUIREMENTS.txt') as f:
    REQUIRED = f.read().splitlines()
# CLASSIFIERS
with open('CLASSIFIERS.txt') as f:
    CLASSIFIED = f.read().splitlines()
# AUTHORS
with open('AUTHORS.txt') as f:
    DATA = f.read().splitlines()
    AUTHORS = ','.join([i.split('::')[0] for i in DATA])
    AUTHORS_EMAIL = ','.join([i.split('::')[1] for i in DATA])

setup(
    name=NAME,
    version=VERSION,
    packages=find_packages(),
    author=AUTHORS,
    author_email=AUTHORS_EMAIL,
    description=DESC,
    long_description=LONG_DESC,
    long_description_content_type='text/markdown',
    include_package_data=True,
    install_requires=REQUIRED,
    url=URLPKG,
    classifiers=CLASSIFIED,
    entry_points={},
    zip_safe=False,
    platforms='any'
)
