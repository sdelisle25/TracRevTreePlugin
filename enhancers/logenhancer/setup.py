#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2008 Emmanuel Blot <emmanuel.blot@free.fr>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.com/license.html.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://projects.edgewall.com/trac/.

from setuptools import setup, find_packages

PACKAGE = 'TracRevtreeLogEnhancer'
VERSION = '2.0'

setup (
    name = PACKAGE,
    version = VERSION,
    description = 'Enhancer for the RevtreePlugin, based on custom log messages',
    author = 'Emmanuel Blot',
    author_email = 'emmanuel.blot@free.fr',
    license='BSD',
    url='http://trac-hacks.org/wiki/RevtreePlugin/LogEnhancer',
    keywords = "trac revision svg graphical tree browser log",
    install_requires = [ 'TracRevtreePlugin >= 1.5dev'],
    packages = find_packages(exclude=['ez_setup', '*.tests*']),
    entry_points = {
        'trac.plugins': [
            'revtree.enhancer = logenhancer'
        ]
    }
)
