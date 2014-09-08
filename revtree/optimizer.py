# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2007 Emmanuel Blot <emmanuel.blot@free.fr>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.com/license.html.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://projects.edgewall.com/trac/.
#

from revtree.api import IRevtreeOptimizer
from trac.core import *

__all__ = ['DefaultRevtreeOptimizer']


class DefaultRevtreeOptimizer(Component):

    """Default optmizer"""

    implements(IRevtreeOptimizer)

    def _get_branch(self, branches, name):
        for branch in branches:
            if branch.branch == name:
                return branch

    def optimize(self, repos, branches):
        """Computes the optimal placement of branches.

        Optimal placement is recommended to reduce the number of operation
        links that cross each other on the rendered graphic.
        This rudimentary example is FAR from providing optimal placements...
        """
        # FIXME: really stupid algorithm
        graph = {}
        branches.sort(lambda a, b: cmp(a.branch, b.branch))
        for branch in branches:
            _b, path = branch.branch, branch.srcpath

            src_branch = self._get_branch(branches, path)
            if not path or not src_branch:
                continue

            if src_branch in graph:
                graph[src_branch].append(branch)
            else:
                graph[src_branch] = [branch]

        density = []
        for (p, v) in graph.items():
            density.append((p, len(v)))

        density.sort(lambda a, b: cmp(a[1], b[1]), reverse=True)
        order = []
        cur = 0
        for (branch, _weight) in density:
            order.insert(cur, branch)
            if cur:
                cur = 0
            else:
                cur = len(order)

        # TODO: work directly with branches
        nbranches = []
        for br in graph.values():
            nbranches.extend(br)

        nbranches.extend([br for br in branches if br not in nbranches])

        for branch in nbranches:
            if branch in order:
                continue
            order.insert(cur, branch)
            if cur:
                cur = 0
            else:
                cur = len(order)
        return order
