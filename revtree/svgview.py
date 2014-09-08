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

from revtree.api import *
from trac.core import *
#  from . import SVGdraw as SVG


__all__ = ['SvgColor', 'SvgGroup', 'SvgOperation', 'SvgRevtree']


class SvgChangeset(object):

    """Changeset/revision node"""

    def __init__(self, rev, clause=None):
        super(SvgChangeset, self).__init__()

        self._classes = []
        self._rev = rev
        self._firstrev = False
        self._lastrev = False
        self._srcrev = None
        self._clause = clause
        self._brings = None
        self._delivers = None
        self._tags = []

    def mark_first(self):
        """Marks the changeset as the first of the branch.
           Inverts the background and the foreground color"""
        self._firstrev = True

    def mark_last(self):
        """Mark the changeset as the latest of the branch"""
        self._lastrev = True

    def set_src(self, path, rev):
        self._srcrev = rev

    def set_brings(self, revs):
        self._brings = list(revs)

    def set_delivers(self, revs):
        self._delivers = list(revs)

    def add_tag(self, tag):
        self._tags.append(tag.prettyname)

    def export(self):
        chgset = dict(rev=self._rev)

        if self._clause is not None:
            chgset.update(clause=self._clause)

        if self._srcrev is not None:
            chgset.update(src=self._srcrev)

        if self._firstrev:
            chgset.update(firstrev=True)

        if self._lastrev:
            chgset.update(lastrev=True)

        if self._brings:
            chgset.update(brings=self._brings)

        if self._delivers:
            chgset.update(delivers=self._delivers)

        if self._tags:
            chgset.update(tags=self._tags)

        return chgset

    def urlbase(self):
        return self._parent.urlbase()


class SvgBranch(object):

    """Branch (set of changesets which whose commits share a common base
       directory)"""

    def __init__(self, parent, branch, style):
        self._parent = parent
        self._branch = branch

        self._svgchangesets = {}
        self._tags = []
        self._lastrev = True

        # Branch revisions
        brc_revisions = branch.get_revisions()

        # Branch revisions to display
        revisions = filter(lambda r, mn=parent.revrange[0],
                           mx=parent.revrange[1]:
                           (mn <= r <= mx) and (r not in parent.filtered_revisions), brc_revisions)
        revisions.sort(reverse=True)

        # Display arrow under branch name to indicate that more recent
        # revisions exist but not displayed
        if revisions[0] < brc_revisions[0]:
            self._lastrev = False

        def _get_clause(rev):
            # Get clause if any
            for r, c in parent.revisions:
                if r == rev:
                    return c
            return None

        self._svgchangesets = [SvgChangeset(rev, _get_clause(rev)) \
                               for rev in revisions]

    def export(self):
        # Export branch changesets
        revisions = [chgset.export() for chgset in self._svgchangesets]

        return dict(name=self._branch.name,
                    path=self._branch.branch,
                    revisions=revisions,
                    lastrev=self._lastrev)

    def create_tag(self, tag):
        svgcs = self.svgchangeset(tag.revision)

        svgcs.add_tag(tag)

    def svgchangeset(self, rev):
        for chgset in self._svgchangesets:
            if chgset._rev == rev:
                return chgset
        return None

    def branch(self):
        return self._branch

    def fontname(self):
        return self._parent.fontname

    def urlbase(self):
        return self._parent.urlbase()


class SvgRevtree(object):

    """Main object that represents the revision tree as a SVG graph"""

    def __init__(self, env, repos, urlbase, enhancers, optimizer):
        """Construct a new SVG revision tree"""
        # Environment
        self.env = env
        # URL base of the repository
        self.url_base = urlbase
        # Repository instance
        self.repos = repos
        # Range of revision to process
        self.revrange = None
        # Optional enhancers
        self.enhancers = enhancers
        # Optimizer
        self.optimizer = optimizer
        # Trunk branches
        self.trunks = self.env.config.get('revtree', 'trunks',
                                          'trunk').split(' ')
        # Dictionary of branch widgets (branches as keys)
        self._svgbranches = {}
        # Markers
        # List of inter branch operations

        # List of changeset groups
        # Operation points
        # Add-on elements (from enhancers)
        self._addons = []
        self._rendering_svgbranches = None

    def svgbranch_ex(self, branchname=None, branch=None, rev=None):
        """Return a branch widget, based on the revision number or the
           branch id"""
        if branchname:
            branches = []
            for b in self._svgbranches.iterkeys():
                if b.branch == branchname:
                    branches.append(self._svgbranches[b])
            return branches

        if rev:
            for b in self._svgbranches.iterkeys():
                if rev in b.get_revisions():
                    return self._svgbranches[b]
            else:
                return None

        return self._svgbranches.get(branch, None)

        if branch not in self._svgbranches:
            return None

        return self._svgbranches[branch]

    def svgbranches(self):
        return self._svgbranches

    def create(self, req, svgbranches, revisions, filtered_revisions, style):
        '''

        :param req:
        :param svgbranches:
        :param revisions: revisions list in reversed order
        :param style:
        '''

        self.revrange = (revisions[-1][0], revisions[0][0])
        self.revisions = revisions
        self.filtered_revisions = filtered_revisions
        self.max_rev = self.revrange[1]

        # Build SVG branches
        for branch_name in svgbranches:
            # REMARK: possibly multiple branches with same name, case created,
            # deleted and recreated
            for branch in self.repos.get_branch(branch_name):
#                 # Filter deleted branch
#                 if not showdeletedbranch and branch.terminalrev:
#                     continue

                # filter if branch has got some revisions in revrange
                brev = filter(lambda r, mn=self.revrange[0],
                              mx=self.revrange[1]:
                              (mn <= r <= mx) and (r not in self.filtered_revisions), branch.get_revisions())
                if brev:
                    self._svgbranches[branch] = SvgBranch(self, branch, style)

        for enhancer in self.enhancers:
            self._addons.append(enhancer.create(self.env, req,
                                                self.repos, self,
                                                self.revrange,
                                                self.filtered_revisions))
        for tag in self.repos.get_tags():
            self.env.log.info("Found tag: %r" % tag.name)

            # Verify revision is in range
            if not (self.revrange[0] <= tag.revision <= self.revrange[-1]):
                continue

            svgbr = self.svgbranch_ex(rev=tag.revision)
            if svgbr:
                svgbr.create_tag(tag)

    def build(self):
        """Build the graph"""
        branches = self.optimizer.optimize(self.repos,
                                           [svgbr.branch() for svgbr in
                                            self._svgbranches.values()])

        # Branches to render
        self._rendering_svgbranches = [self.svgbranch_ex(branch=b) for b in branches]
        if not self._rendering_svgbranches:
            raise EmptyRangeError

    def export(self):
        return [brc.export() for brc in self._rendering_svgbranches]

    def urlbase(self):
        return self.url_base

