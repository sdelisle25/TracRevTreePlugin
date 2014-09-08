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
#

from revtree.api import IRevtreeEnhancer, RevtreeEnhancer
# from revtree.svgview import SvgOperation
from trac.core import *

__all__ = ['SimpleEnhancerModule']


class SimpleEnhancer(RevtreeEnhancer):

    """This class is a very basic skeleton that needs to customized, to
       provide SvgOperation, SvgGroup and other widgets in the RevTree graphic
    """

    def __init__(self, env, req, repos, svgrevtree, revisions):
        """Creates the internal data from the repository"""
        self.creations = []
        self.svgrevtree = svgrevtree
        # z-depth indexed widgets
        self._widgets = [[] for l in IRevtreeEnhancer.ZLEVELS]
        svgbranches = self.svgrevtree.svgbranches()
        for branch, svgbranch in svgbranches.iteritems():
            firstchgset = branch.firstrev
            # if the first changeset of a branch is a copy of another
            # changeset(from another branch)
            if (firstchgset in revisions) and branch.srcpath:
                # tweak the appearance of this changeset ..
                svgbranch.svgchangeset(firstchgset).mark_first()
                (rev, path) = int(branch.srcrev), branch.srcpath

                if rev in revisions:
                    self.creations.append((path, rev,
                                           branch.branch, firstchgset))

            # Terminate branch revision
            if branch.terminalrev and branch.terminalrev in revisions:
                svgbranch.svgchangeset(branch.terminalrev).mark_last()

    def build(self):
        """Build the enhanced widgets"""
        for (srcpath, srcrev, dstpath, dstrev) in self.creations:
            svgsrcbr = self.svgrevtree.svgbranch_ex(branchname=srcpath)
            if not svgsrcbr:
                continue

            for item in svgsrcbr:
                svgsrcchg = item.svgchangeset(srcrev)
                if svgsrcchg:
                    break
            else:
                continue

            svgdstbr = self.svgrevtree.svgbranch_ex(branchname=dstpath)
            if not svgdstbr:
                continue

            for item in svgdstbr:
                svgdstchg = item.svgchangeset(dstrev)
                if svgdstchg:
                    break

#             op = SvgOperation(self.svgrevtree, svgsrcchg, svgdstchg, '#3f3f3f')
#             self._widgets[IRevtreeEnhancer.ZMID].append(op)

        for wl in self._widgets:
            map(lambda w: w.build(), wl)

    def render(self, level):
        """Renders the widgets, from background plane to foreground plane"""
        if level < len(IRevtreeEnhancer.ZLEVELS):
            map(lambda w: w.render(), self._widgets[level])


class SimpleEnhancerModule(Component):

    """Enhance the appearance of the RevTree with site-specific properties.

    Create branch clone operation (on branch/tag operations)

    This class is a very basic skeleton that needs to customized, to provide
    SvgOperation, SvgGroup and other widgets in the RevTree graphic
    """

    implements(IRevtreeEnhancer)

    def create(self, env, req, repos, svgrevtree, revisions):
        return SimpleEnhancer(env, req, repos, svgrevtree, revisions)
