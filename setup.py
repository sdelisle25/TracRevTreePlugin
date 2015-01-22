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

PACKAGE = 'TracRevtreePlugin'
VERSION = '2.0.1'

setup(
    name=PACKAGE,
    version=VERSION,
    description='Revision graph visualizer for the Trac VCS browser',
    author='Emmanuel Blot',
    author_email='emmanuel.blot@free.fr',
    license='BSD',
    url='http://trac-hacks.org/wiki/RevtreePlugin',
    keywords="trac revision svg graphical tree browser visual",
    install_requires=['Trac>=0.12dev', 'Trac<1.2'],
    packages=find_packages(exclude=['ez_setup', '*.tests*', '*.enhancers.*']),
    package_data={
        'revtree': [
            'htdocs/css/*.css',
            'htdocs/js/*.js',
            'htdocs/images/*.gif',
            'templates/*.html'
            'templates/*.svg'
        ]
    },
    entry_points={
        'trac.plugins': [
            'revtree.web_ui = revtree.web_ui',
            'revtree.enhancer = revtree.enhancer',
            'revtree.optimizer = revtree.optimizer',
            'revtree.db = revtree.db',
            'revtree.admin = revtree.admin',
            'revtree.rhs_hooks = revtree.rhs_hooks'
        ]
    }
)
