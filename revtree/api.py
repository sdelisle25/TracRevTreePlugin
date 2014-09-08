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

from trac.config import ExtensionOption
from trac.core import *

__all__ = ['IRevtreeEnhancer', 'IRevtreeOptimizer', 'RevtreeEnhancer',
           'EmptyRangeError', 'BranchPathError', 'RevtreeSystem']


class RevtreeEnhancer(object):

    """Enhancer interface"""

    def build(self):
        """Build the widgets"""
        raise NotImplementedError

    def render(self, level):
        """Render the widgets"""
        raise NotImplementedError


class IRevtreeEnhancer(Interface):

    """Provide graphical enhancements to a revision tree"""

    # Rendering Z levels
    (ZBACK, ZMID, ZFORE) = ZLEVELS = range(3)

    def create(env, req, repos, svgrevtree):
        """Create the internal data from the repository
           Return a RevtreeEnhancer instance
        """


class IRevtreeOptimizer(Interface):

    """Provide optimized location for revision tree elements"""

    def optimize_branches(repos, branches):
        """Sort the branch elements.

        Return an placement ordered list, from the left-most to the right-most
        branch.
        """


class EmptyRangeError(TracError):

    """Defines a RevTree error (no changeset in the selected range)"""

    def __init__(self, msg=None):
        TracError.__init__(self, "%sNo changeset"
                           % (msg and '%s: ' % msg or ''))


class BranchPathError(TracError):

    """Defines a RevTree error (incoherent paths in a branch)"""

    def __init__(self, msg=None):
        TracError.__init__(self, "Incoherent path %s" % (msg or ''))


class RevtreeSystem(Component):

    """Revision tree constructor"""

    enhancers = ExtensionPoint(IRevtreeEnhancer)
    optimizer = ExtensionOption('revtree', 'optimizer', IRevtreeOptimizer,
                                'DefaultRevtreeOptimizer',
        """Name of the component implementing `IRevtreeOptimizer`, which is
        used for optimizing revtree element placements.""")

    def get_revtree(self, repos, req):
        # ideally, the repository type should be requested from the repos
        # instance; however it is usually hidden behind the repository cache
        # that does not report the actual repository backend
        if self.config.get('trac', 'repository_type') != 'svn':
            raise TracError("Revtree only supports Subversion repositories")

        self.env.log.debug("Enhancers: %s" % self.enhancers)

        from revtree.svgview import SvgRevtree

        return SvgRevtree(self.env, repos, req.href(),
                          self.enhancers, self.optimizer)
