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

from revtree import IRevtreeEnhancer, RevtreeEnhancer
from trac.core import *

__all__ = ['LogEnhancerModule']


class LogEnhancer(RevtreeEnhancer):
    """Revtree enhancer based on specific log messages and custom properties
    This class is provided as-is, as an example

    'rth' stands for 'RevTree Hack', as I've been unable to come with a
    better name.
    """

    def __init__(self, env, req, repos, svgrevtree, revrange, filtered_revisions):
        """Creates the internal data from the repository"""
        self.env = env
        self._repos = repos
        self._svgrevtree = svgrevtree
        self._revrange = revrange
        self._filtered_revisions = filtered_revisions

        svgbranches = self._svgrevtree.svgbranches()
        for branch, svgbranch in svgbranches.iteritems():
            firstchgset = branch.firstrev

            if (revrange[0] <= firstchgset <= revrange[1])and \
             (firstchgset not in self._filtered_revisions) \
             and branch.srcpath:
                # tweak the appearance of this changeset ..
                svgbranch.svgchangeset(firstchgset).mark_first()
                (rev, path) = int(branch.srcrev), branch.srcpath

                if (revrange[0] <= rev <= revrange[1]) and \
                    (rev not in self._filtered_revisions):
                    svgbranch.svgchangeset(firstchgset).set_src(path, rev)

            # Terminate branch revision
            if branch.terminalrev and \
               (revrange[0] <= branch.terminalrev <= revrange[1]) and \
               (branch.terminalrev not in self._filtered_revisions):
                svgbranch.svgchangeset(branch.terminalrev).mark_last()

            # Delivers information for this branch
            for deliver in self._repos.get_delivers(branch.branch):
                # Is branch revision is valid ?
                if not (revrange[0] <= deliver.revision <= revrange[1]):
                    continue

                if (deliver.revision in self._filtered_revisions):
                    continue

                revs = deliver.get_revisions()

                # SVG branch source exist
                svgsrc = self._svgrevtree.svgbranch_ex(rev=revs[-1])
                if not svgsrc:
                    continue

                # Branch source
                branchsrc = svgsrc.branch()

                # filter available revision for branch source
                branchsrc_rev = filter(lambda r: (revrange[0] <= r <= revrange[1]) \
                                       and (r not in filtered_revisions),
                                       branchsrc.get_revisions())

                brrevs = [r for r in revs if r in branchsrc_rev]
                if not brrevs:
                    continue

                brrevs.sort()
                fchg_rev = brrevs[0]
                lchg_rev = brrevs[-1]

                # REMARK: multiple branch name can exist in case of
                # multiple delete creation so current branch can be the wrong
                # branch for deliver revision we must test if chgset is not None
                chgset = svgbranch.svgchangeset(deliver.revision)
                if chgset:
                    chgset.set_delivers((lchg_rev, fchg_rev))

            # Brings information for this branch
            for bring in self._repos.get_brings(branch.branch):
                svgsrc = self._svgrevtree.svgbranch_ex(branchname=bring.branch)
                if not svgsrc:
                    continue

                # Is branch revision is valid ?
                if not (revrange[0] <= bring.revision <= revrange[1]):
                    continue

                if (bring.revision in self._filtered_revisions):
                    continue

                revs = bring.get_revisions()

                # SVG branch source exist
                svgsrc = self._svgrevtree.svgbranch_ex(rev=revs[-1])
                if not svgsrc:
                    continue

                # Branch source
                branchsrc = svgsrc.branch()

                # filter available revision for branch source
                branchsrc_rev = filter(lambda r: revrange[0] <= r <= revrange[1] \
                                       and (r not in filtered_revisions),
                                       branchsrc.get_revisions())

                brrevs = [r for r in revs if r in branchsrc_rev]
                if not brrevs:
                    continue

                brrevs.sort()
                fchg_rev = brrevs[0]
                lchg_rev = brrevs[-1]

                chgset = svgbranch.svgchangeset(bring.revision)
                if chgset:
                    chgset.set_brings((lchg_rev, fchg_rev))


class LogEnhancerModule(Component):
    """Revtree enhancer based on specific log messages and custom properties
    """

    implements(IRevtreeEnhancer)

    def create(self, env, req, repos, svgrevtree, revrange, filtered_revisions):
        return LogEnhancer(env, req, repos, svgrevtree, revrange, filtered_revisions)

