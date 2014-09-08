# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Emmanuel Blot <emmanuel.blot@free.fr>
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
# from revtree.svgview import SvgOperation, SvgGroup
from trac.core import *
from trac.util.text import to_unicode

__all__ = ['MergeInfoEnhancerModule']


class MergeInfoEnhancer(RevtreeEnhancer):
    """Enhancer to show merge operation, based on svn:mergeinfo properties.
    """

    def _get_merge_src_info(self, path, rev):
        """Extract merge information as a list"""
        srcmergeprops = set()

#        srcbranch = self._svgrevtree.svgbranch_ex(rev=rev)
        srcbranch = self._repos.get_branch(path, rev=rev)
        if srcbranch:
            branch = srcbranch[0]
            if branch.srcpath:
                (srev, spath) = int(branch.srcrev), branch.srcpath
                srcmergeprops = self._get_merge_src_info(spath, srev)

        props = self._repos.get_node_properties(path, rev)
        mergeprop = props and props.get('svn:mergeinfo') or ''

        for item in mergeprop.split('\n'):
            srcmergeprops.add(item)

        return srcmergeprops

    def _get_merge_info(self, branch, rev):
        """Extract merge information as a list"""
        # Get branch revision merge information
        props = self._repos.get_node_properties(branch.branch, rev)
        mergeprop = props and props.get('svn:mergeinfo')
        if not mergeprop:
            return []

        return mergeprop.split('\n')

    def __init__(self, env, req, repos, svgrevtree, revrange, filtered_revisions):
        """Creates the internal data from the repository"""
        self._repos = repos
        self._svgrevtree = svgrevtree
        self._widgets = [[] for l in IRevtreeEnhancer.ZLEVELS]
        self._merges = []
        self._groups = []
        self._creations = []
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

            chgsets = [rev for rev in branch.get_revisions() \
                       if (revrange[0] <= rev <= revrange[1]) and
                       (rev not in self._filtered_revisions)]
            chgsets.sort()

            # Get source branch merge information if any
            srcmergeprops = []
            if branch.srcpath:
                srcmergeprops = self._get_merge_src_info(branch.srcpath,
                                                         int(branch.srcrev))
                srcmergeprops = list(srcmergeprops)

            mergeops = []
            for rev in chgsets:
                if branch.terminalrev == rev:  # REMARK: not more branch on terminal revision
                    continue

                mergeprops = self._get_merge_info(branch, rev)
                mergeprops = [mp for mp in mergeprops if mp not in srcmergeprops]

                if mergeprops:
                    mergeops.append((rev, [m for m in mergeprops]))

            # MANDATORY: merge information must be sorted
            mergeops.sort(cmp=lambda a, b: cmp(a[0], b[0]))

            #prevmerge = None
            merge_revs = []
            for rev, merges in mergeops:
                for source in merges:
                    (srcbr, srcrev) = source.split(':')

                    # Fast completion if branch not in svgbranch to display
                    srcbranch = self._svgrevtree.svgbranch_ex(branchname=to_unicode(srcbr[1:]))
                    if not srcbranch:
                        continue

                    for srcrange in srcrev.split(','):
                        srcs = srcrange.split('-')
                        s1 = int(srcs[0])
                        s2 = int(len(srcs) > 1 and srcs[1] or srcs[0])

                        # Filter already merged revisions
                        revs = [r for r in xrange(s1, s2 + 1) if r not in merge_revs]
                        if not revs:
                            continue

                        s1 = revs[0]
                        s2 = revs[-1]

                        merge_revs.extend(revs)

                        # srcbranch = repos.get_branch(to_unicode(srcbr[1:]))
                        svgsrcbranch = self._svgrevtree.svgbranch_ex(rev=s1)
                        if not svgsrcbranch:
                            continue

                        srcbrc = svgsrcbranch.branch()
                        srcrevs = srcbrc.get_revisions()
                        srcrevs.sort()
                        srcrevs = filter(lambda x: s1 <= x <= s2, srcrevs)
                        if not srcrevs:
                            continue

                        fchg = srcrevs[0]
                        lchg = srcrevs[-1]

                        cchg = rev
                        self._groups.append((srcbrc.branch, fchg, lchg))
                        self._merges.append((lchg, cchg))

                        svgbranch_src = self._svgrevtree.svgbranch_ex(branchname=srcbrc.branch)
                        if not svgbranch_src:
                            continue

                        for b in svgbranch_src:
                            fsvg = b.svgchangeset(fchg)
                            lsvg = b.svgchangeset(lchg)
                            if fsvg and lsvg:
                                break
                        else:
                            continue

                        # SVG branches
                        svgsrcbr = self._svgrevtree.svgbranch_ex(rev=lchg)
                        svgdstbr = self._svgrevtree.svgbranch_ex(rev=cchg)
                        if not svgsrcbr or not svgdstbr:
                            continue

                        # REMARK: multiple branch name can exist in case of
                        # multiple delete creation so current branch can be the wrong
                        # branch for deliver revision we must test if chgset is not None
                        chgset = svgbranch.svgchangeset(cchg)
                        if chgset:
                            chgset.set_delivers((lchg, fchg))


class MergeInfoEnhancerModule(Component):
    """Enhancer to show merge operation, based on svn:mergeinfo properties.

       This enhancer requires a SVN >= 1.5 repository. Previous releases of
       SVN do not manage the required information. This enhancer cannnot be
       used with repositories managed with the svnmerge.py tool
    """

    implements(IRevtreeEnhancer)

    def create(self, env, req, repos, svgrevtree, revrange, filtered_revisions):
        return MergeInfoEnhancer(env, req, repos, svgrevtree, revrange,
                                 filtered_revisions)
