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

    def __init__(self, env, req, repos, svgrevtree, revrange):
        """Creates the internal data from the repository"""
        self._repos = repos
        self._svgrevtree = svgrevtree
        self._widgets = [[] for l in IRevtreeEnhancer.ZLEVELS]
        self._merges = []
        self._groups = []
        self._creations = []
        self._revrange = revrange

        svgbranches = self._svgrevtree.svgbranches()
        for branch, svgbranch in svgbranches.iteritems():
            firstchgset = branch.firstrev

            if (revrange[0] <= firstchgset <= revrange[1]) and branch.srcpath:
                # tweak the appearance of this changeset ..
                svgbranch.svgchangeset(firstchgset).mark_first()
                (rev, path) = int(branch.srcrev), branch.srcpath

                if revrange[0] <= rev <= revrange[1]:
                    self._creations.append((path, rev,
                                           branch.branch, firstchgset))

            # Terminate branch revision
            if branch.terminalrev and \
               (revrange[0] <= branch.terminalrev <= revrange[1]):
                svgbranch.svgchangeset(branch.terminalrev).mark_last()

            chgsets = [rev for rev in branch.get_revisions() \
                       if revrange[0] <= rev <= revrange[1]]
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
            for m in mergeops:
                (rev, merges) = m

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
                #prevmerge = merges

    def build(self):
        """Build the enhanced widgets"""
        for (srcpath, srcrev, dstpath, dstrev) in self._creations:
            # Is SVG source branch exist
            svgsrcbr = self._svgrevtree.svgbranch_ex(branchname=srcpath)
            svgdstbr = self._svgrevtree.svgbranch_ex(branchname=dstpath)
            if not svgsrcbr or not svgdstbr:
                continue

            # SVG source changeset
            for item in svgsrcbr:
                svgsrcchg = item.svgchangeset(srcrev)
                if svgsrcchg:
                    break
            else:
                continue

            # SVG destination changeset
            for item in svgdstbr:
                svgdstchg = item.svgchangeset(dstrev)
                if svgdstchg:
                    break
            else:
                continue

            op = SvgOperation(self._svgrevtree, svgsrcchg, svgdstchg, '#3f3f3f')
            self._widgets[IRevtreeEnhancer.ZMID].append(op)

        # Groups
        for (branch_name, first, last) in self._groups:
            svgbranch = self._svgrevtree.svgbranch_ex(branchname=branch_name)
            if not svgbranch:
                continue

            for b in svgbranch:
                fsvg = b.svgchangeset(first)
                lsvg = b.svgchangeset(last)
                if fsvg and lsvg:
                    break
            else:
                continue

            group = SvgGroup(self._svgrevtree, fsvg, lsvg)
            self._widgets[IRevtreeEnhancer.ZBACK].append(group)

        # Merges
        for (srcchg_rev, dstchg_rev) in self._merges:
            # SVG branches
            svgsrcbr = self._svgrevtree.svgbranch_ex(rev=srcchg_rev)
            svgdstbr = self._svgrevtree.svgbranch_ex(rev=dstchg_rev)
            if not svgsrcbr or not svgdstbr:
                continue

            # SVG changesets
            svgsrcchg = svgsrcbr.svgchangeset(srcchg_rev)
            svgdstchg = svgdstbr.svgchangeset(dstchg_rev)
            if not svgsrcchg or not svgdstchg:
                continue

            op = SvgOperation(self._svgrevtree, svgsrcchg, svgdstchg, 'orange')
            self._widgets[IRevtreeEnhancer.ZMID].append(op)

        for wl in self._widgets:
            map(lambda w: w.build(), wl)

    def render(self, level):
        """Renders the widgets, from background plane to foreground plane"""
        if level < len(IRevtreeEnhancer.ZLEVELS):
            map(lambda w: w.render(), self._widgets[level])


class MergeInfoEnhancerModule(Component):
    """Enhancer to show merge operation, based on svn:mergeinfo properties.

       This enhancer requires a SVN >= 1.5 repository. Previous releases of
       SVN do not manage the required information. This enhancer cannnot be
       used with repositories managed with the svnmerge.py tool
    """

    implements(IRevtreeEnhancer)

    def create(self, env, req, repos, svgrevtree, revrange):
        return MergeInfoEnhancer(env, req, repos, svgrevtree, revrange)
