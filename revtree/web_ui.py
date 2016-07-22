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

from genshi.builder import tag
from revtree.api import RevtreeSystem, EmptyRangeError
from revtree.model import Repository
from trac.admin.api import get_console_locale
from trac.config import (Option, IntOption, BoolOption, ListOption,
                         ConfigurationError)
from trac.core import *
from trac.perm import IPermissionRequestor
from trac.util.datefmt import (format_datetime, pretty_timedelta, to_timestamp,
                               get_date_format_hint, parse_date)
from trac.util.text import to_unicode
from trac.util.translation import _
from trac.web import IRequestFilter, IRequestHandler
from trac.web.chrome import add_ctxtnav, add_script, add_stylesheet, \
    INavigationContributor, ITemplateProvider, add_script_data, add_warning, Chrome
from trac.wiki import wiki_to_html
import cProfile
import json
import re
import time


def profiler(func):
    def profiled_func(*args, **kwargs):
        profile = cProfile.Profile()
        try:
            profile.enable()
            result = func(*args, **kwargs)
            profile.disable()
            return result
        finally:
            profile.dump_stats("/tmp/profile.txt")
    return profiled_func

__all__ = ['RevtreeModule']


class QueryFilter(object):
    clause_re = re.compile(r'(?P<clause>\d+)_(?P<constraint>.+)$')
    constaint_names = ['author',
                       'branch',
                       'period',
                       'revision',
                       'date',
                       'deleted_branches']

    def __init__(self, env, repos, query_info):
        self.clauses = dict()
        self._query_changeset = None
        self._query_branch = None
        self._query_clauses = None
        self._env = env
        self._repos = repos

        self._filtered_revisions = set()

        # Deleted branches, prepare revisions filter
        self._deleted_revisions = set()
        for branch in repos.get_branches():
            if branch.terminalrev:
                self._deleted_revisions.update(branch.get_revisions())

        # Build internal representation
        self._build(query_info)

    def filtered_revisions(self):
        return self._filtered_revisions

    def _date_convert(self, date_str):
        try:
            locale = get_console_locale(self._env)
            return to_timestamp(parse_date(date_str, hint='date',
                                           locale=locale))
        except Exception as excpt:
            self._env.log.exception(excpt)
            raise EmptyRangeError(excpt.message)

    def _filter_deleted_branches(self, flag, rev):
        """
        Filter deleted branch, if flag is True, accept all branches even if
        deleted. Otherwise if revision is owned by deleted branch, revision
        is rejected.

        :param flag:
        :param rev:
        """

        if flag is True:
            return True

        if rev in self._deleted_revisions:
            self._filtered_revisions.add(rev)
            return False

        return True

    def _build(self, query_info):
        for k, vals in query_info.iteritems():
            match = self.clause_re.match(k)
            if not match:
                continue
            constraint = match.group('constraint')
            clause_id = match.group('clause')
            if constraint not in self.constaint_names:
                continue
            if not isinstance(vals, (list, tuple)):
                vals = [vals]
            if vals:
                # For corresponding clause add constraint
                clause = self.clauses.setdefault(int(clause_id), {})
                if constraint == 'revision':
                    gen = iter(vals)
                    vals = [(int(v), int(gen.next())) for v in gen]
                elif constraint == 'date':
                    gen = iter(vals)
                    vals = [(v, gen.next()) for v in gen]
                clause.setdefault(constraint, []).extend(vals)

        # Clauses
        self.clauses = [self.clauses[clause_id]
                        for clause_id in sorted(self.clauses.keys())]
        for clause in self.clauses:
            clause.setdefault("deleted_branches", ["False"])

        rule_query_formatter = {
            'author': lambda v:
              "True if '' in %s else [a for a in authors if a in %s]" % (v, v),

            'period': lambda v:
            ' or '.join(
                ['((( (timebase - (%d * 86400)) <= date) and (date <= '
                 'timebase)) if %s else True)' % (int(p), int(p)) for p in v]),

            'branch': lambda v: "True if 'all' in %s else branch in %s" %
            (v, v),

            'revision': lambda v:
              " or ".join(['((%d <= rev) and (rev <= %d))' % i for i in v]),

            'deleted_branches': lambda v:
                " or ".join(['filter_deleted_branches(%s, rev)' % f for f in v]),

            'date': lambda v:
              " or ".join(
                ['( (date_convert("%s") <= date) and '
                 '  (date <= date_convert("%s")) )' % (f, t) for f, t in v]),
        }

        def rule_query(rule_name, value):
            """
            Build clause rule query
            """
            return rule_query_formatter.get(rule_name)(value)

        def clause_query(clause):
            """
            Build clause query
            """
            return " and ".join(['(%s)' % rule_query(n, v)
                                 for n, v in clause.iteritems()])

        self._query_clauses = [compile(clause_query(cts), 'query', 'eval')
                               for cts in self.clauses]

    def eval(self, branch, authors, revision, date, timebase):
        params = dict(rev=revision,
                      date=date,
                      branch=branch,
                      authors=authors,
                      timebase=timebase,
                      date_convert=self._date_convert,
                      filter_deleted_branches=self._filter_deleted_branches)
        for idx, clause in enumerate(self._query_clauses):
            if eval(clause, params):
                # Is revision has been filtered by an other clause, restore it
                if revision in self._filtered_revisions:
                    self._filtered_revisions.remove(revision)

                return idx + 1, True
        return None, False

    def export(self):
        return self.clauses


class FloatOption(Option):

    """Descriptor for float configuration options.
       Option for real number is missing in Trac
    """

    def accessor(self, section, name, default=0.0):
        """Return the value of the specified option as float.

        If the specified option can not be converted to a float, a
        `ConfigurationError` exception is raised.

        Valid default input is a string or a float. Returns an float.
        """
        value = section.get(name, default)
        try:
            return float(value)
        except ValueError:
            raise ConfigurationError('Expected real number, got %s' % \
                                     repr(value))


class ChoiceOption(Option):

    """Descriptor for choice configuration options."""

    def __init__(self, section, name, default=None, choices='', doc=''):
        Option.__init__(self, section, name, default, doc)
        self.choices = filter(None, [c.strip() for c in choices.split(',')])

    def accessor(self, section, name, default):
        value = section.get(name, default)
        if value not in self.choices:
            raise ConfigurationError('expected a choice among "%s", got %s' %
                                     (', '.join(self.choices), repr(value)))
        return value


class SessionContext(object):

    def __init__(self, req, *args, **kwargs):
        self._req = req
        self._data = eval(self._req.session.get('revtree', '{}'))

    def clear(self):
        self._data = {}
        self._req.session['revtree'] = str(self._data)

    def __getitem__(self, item):
        return self._data.get(item, None)

    def __setitem__(self, item, value):
        self._data[item] = value
        self._req.session['revtree'] = str(self._data)


class RevtreeModule(Component):

    """Implements the revision tree feature"""

    implements(IPermissionRequestor, INavigationContributor,
               IRequestFilter, IRequestHandler, ITemplateProvider)

    reg_expr = re.compile(r'^\w+/t(\d+)\w*$')

    # Timeline ranges
    PERIODS = {0: 'all', 1: 'day', 2: '2 days', 3: '3 days', 5: '5 days',
               7: 'week', 14: 'fortnight', 31: 'month', 61: '2 months',
               91: 'quarter', 183: 'semester', 366: 'year'}

    # Configuration Options
    branchre = Option('revtree', 'branch_re',
                      r'^(?:(?P<branch>trunk|(?:branches|sandboxes|vendor)/'
                      r'(?P<branchname>[^/]+))|'
                      r'(?P<tag>tags/(?P<tagname>[^/]+)))(?:/(?P<path>.*))?$',
        doc="""Regular expression to extract branches from paths""")

    abstime = BoolOption('revtree', 'abstime', 'true',
                         doc="""Timeline filters start on absolute time or
                         on the youngest revision.""")

    contexts = ListOption('revtree', 'contexts',
        doc="""Navigation contexts where the Revtree item appears.
               If empty, the Revtree item appears in the main navigation
               bar.""")

    trunks = ListOption('revtree', 'trunks',
                        doc="""Branches that are considered as trunks""")

    oldest = IntOption('revtree', 'revbase', '1',
                       doc="""Oldest revision to consider
                           (older revisions are ignored)""")

    style = ChoiceOption('revtree', 'style', 'compact', 'compact,timeline',
                         doc="""Revtree style, 'compact' or 'timeline'""")

    scale = FloatOption('revtree', 'scale', '1',
                        doc="""Default rendering scale for the SVG graph""")

    # IPermissionRequestor methods
    def get_permission_actions(self):
        return ['REVTREE_VIEW']

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'revtree'

    def get_navigation_items(self, req):
        if not req.perm.has_permission('REVTREE_VIEW'):
            return
        if self.contexts:
            return
        yield ('mainnav', 'revtree',
               tag.a('Rev Tree', href=req.href.revtree()))

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler

    # IRequestHandler methods
    def match_request(self, req):
        match = re.match(r'/revtree(/revtree_log)?(?:/([^/]+))?',
                         req.path_info)
        if match:
            if match.group(1):
                req.args['logrev'] = match.group(2)
            return True

    # ITemplateProvider
    def get_htdocs_dirs(self):
        """Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc).
        """
        from pkg_resources import resource_filename
        return [('revtree', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        """Return the absolute path of the directory containing the provided
        Genshi templates.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def __init__(self):
        """Reads the configuration and run sanity checks"""
        self.env.log.debug('Revtree RE: %s' % self.branchre)
        self.bcre = re.compile(self.branchre)
        self.rt = RevtreeSystem(self.env)

    def process_request(self, req):
        req.perm.assert_permission('REVTREE_VIEW')
        if 'autocompletion' in req.args:
            return self._process_request_completion(req)

        # Reset clauses
#         if req.args.get('reset'):
#             session_ctx = SessionContext(req)
#             session_ctx.clear()
#             req.redirect(req.href('revtree'))
#             return None

        if 'logrev' in req.args:
            return self._process_log_request(req)

        # AJAX request
        hdr = req.get_header('X-Requested-With')
        if hdr == "XMLHttpRequest":
            return self._process_filter_request(req)

        # Default revision tree page
        return self._process_revtree(req)

    def post_process_request(self, req, template, data, content_type):
        if req.perm.has_permission('REVTREE_VIEW'):
            url_parts = filter(None, req.path_info.split(u'/'))
            if url_parts and (url_parts[0] in self.contexts):
                add_ctxtnav(req, 'Revtree' % self.contexts,
                            href=req.href.revtree())
        return (template, data, content_type)

    def _process_request_completion(self, req):
        '''
        Process branch name completion request.

        This method is invoked filter branch name is modified,
        returning matching branch names.
        '''

        path = req.args.get('autocompletion', '').strip()

        branches = self._get_ui_branches()
        items = [tag.li(brc, class_="deleted" if deleted else "")
                 for brc, deleted in branches if brc.startswith(path)]
        elem = tag.ul(items)

        xhtml = elem.generate().render('xhtml', encoding='utf-8')
        req.send_response(200)
        req.send_header('Content-Type', "text/xml")
        req.send_header('Content-Length', len(xhtml))
        req.write(xhtml)

    def _process_log_request(self, req):
        '''
        Process log request information.

        This method is invoked when cursor is over a RevTree changeset,
        returning corresponding revision log information.

        :param req: Trac request object
        :returns: template, template data, type of response
        '''

        try:
            rev = int(req.args['logrev'])
            repos = Repository.get_svn_repository(self.env)
            if not repos:
                raise TracError("Revtree only supports Subversion "
                                "repositories")
            chgset = repos.get_changeset(rev)
            wikimsg = wiki_to_html(to_unicode(chgset.message),
                                   self.env,
                                   req,
                                   None,
                                   True,
                                   False)
            data = {
                'chgset': True,
                'revision': rev,
                'time': format_datetime(chgset.date).replace('()', ''),
                'age': pretty_timedelta(chgset.date, None, 3600),
                'author': to_unicode(chgset.author) or u'anonymous',
                'message': wikimsg
            }

            return 'revtree_log.html', {'log': data}, 'application/xhtml+xml'
        except Exception as e:
            raise TracError("Invalid revision log request: %s" % e)

    def _process_query(self, repos, query, timebase):
        """

        :param repos:
        :param query:
        :param timebase:
        """

        # REMARK: use set assert not duplicated element
        svgbranches = set()
        revisions = []

        # Filtered revisions
        filtered_revisions = set()
        for rev_item in repos.get_revisions():
            clause_idx, result = query.eval(revision=rev_item.revision,
                                            date=int(rev_item.date),
                                            timebase=timebase,
                                            branch=rev_item.branch,
                                            authors=[rev_item.author, ])
            if not result:
                filtered_revisions.add(rev_item.revision)
                continue

            if rev_item.revision in filtered_revisions:
                filtered_revisions.remove(rev_item.revision)

            # Add branch
            svgbranches.add(rev_item.branch)

            # Add revision and associated clause
            revisions.append((rev_item.revision, clause_idx))

        filtered_revisions = query.filtered_revisions()

        filtered_revisions = set()
        return svgbranches, revisions, filtered_revisions

    def _process_query_filters_options(self, req, key, value):
        '''
        Process filters/options change state.

        This method is invoked when filters/options are collapsed or
        uncollapsed to store their state.

        :param req: Trac request object
        :param key:
        :param value:
        '''

        # Update session information
        session_ctx = SessionContext(req)
        session_ctx[key] = value

        req.send_response(200)
        req.send_header('Content-Type', "text")
        req.send_header('Content-Length', 0)
        req.write('')

    def _process_filter_request(self, req):
        '''
        Process filter request.

        This method is invoked when RevTree update is done by user.

        :param req: Trac request object
        '''
        session_ctx = SessionContext(req)

        # Reset clause
        if req.args.get("reset"):
            session_ctx.clear()

            dump = json.dumps(dict())

            # Send response
            req.send_response(200)
            req.send_header('Content-Type', "application/json")
            req.send_header('Content-Length', len(dump))
            req.write(dump);
            return

        for key in ['query_options', 'query_filters']:
            if key not in req.args:
                continue
            return self._process_query_filters_options(req,
                                                       key,
                                                       req.args[key])

        # Repository object
        repos = Repository(self.env)

        if self.abstime:
            timebase = int(time.time())
        else:
            youngest = repos.get_youngest_rev()
            timebase = to_timestamp(repos.get_changeset(youngest).date)

        # Style options
        style = req.args.get('style', 'compact')

        try:
            # Generate query
            query = QueryFilter(self.env,
                                repos,
                                req.args)

            # Update session context information
            session_ctx['query'] = query.export()
            session_ctx['style'] = style

            svgbranches, revisions, filtered_revisions = \
                self._process_query(repos,
                                    query,
                                    timebase)
            if (not svgbranches) or (not revisions):
                raise EmptyRangeError('')

            repos = Repository(self.env)

            # MANDATORY: revisions must be sorted in reversed order
            revisions.sort(reverse=True, key=lambda t: t[0])

            # SVG revision tree object
            svgrevtree = self.rt.get_revtree(repos, req)
            svgrevtree.create(req,
                              svgbranches,
                              revisions,
                              filtered_revisions,
                              style)

            svgrevtree.build()
        except EmptyRangeError as excpt:
            msg = _('Selected filters cannot '
                    'render a revision tree. %s' % excpt.message.encode('utf8'))
            msg = msg.encode('UTF-8')
            req.send_response(404)
            req.send_header('Content-Type', "text/html; charset=utf-8'")
            req.send_header('Content-Length', len(msg))
            req.write(msg)
        else:
            data = dict(revisions=self._get_ui_revisions(),
                        authors=self._get_ui_authors(),
                        # branches=self._get_ui_branches(reverse=False),
                        fontsize=self.env.config.get('revtree',
                                                     'fontsize',
                                                     '14pt'),
                        fontfamily=self.env.config.get('revtree',
                                                       'fontname',
                                                       'arial'),
                        tree=dict(brc=svgrevtree.export(),
                                  max_rev=svgrevtree.max_rev),
                        url=req.href(),
                        style=style)
            dump = json.dumps(data)

            # Send response
            req.send_response(200)
            req.send_header('Content-Type', "application/json")
            req.send_header('Content-Length', len(dump))
            req.write(dump)

    def _process_revtree(self, req):
        '''
        Process RevTree.

        This method is invoked to display RevTree page.

        :param req: Trac query object
        '''

        session_ctx = SessionContext(req)

        # Reset clause
        if req.args.get("reset"):
            session_ctx.clear()

        # Revisions
        revisions = self._get_ui_revisions()

        # Branches
        branches = [b for b, d in self._get_ui_branches(reverse=False)]

        # Authors
        authors = self._get_ui_authors()

        # Constraints fields name
        fields = {'author': 'author',
                  'branch': 'branch',
                  'revision': 'revision',
                  'period': 'period',
                  'date': 'date',
                  'deleted_branches': 'show deleted branches'}

        # Get session information
        clauses = session_ctx['query'] or [{'period': [u'14'],
                                            'author': [unicode(req.authname or
                                                               'all')]}]

        style = session_ctx['style'] or 'compact'
        query_options = session_ctx['query_options'] or 'false'
        query_filters = session_ctx['query_filters'] or 'false'

        properties = {k: v for k, v in fields.items()}
        periods = self._get_ui_periods()

        # Data for genshi
        data = {'title': 'Revision Tree',
                'fields': fields,
                'clauses': clauses,
                'authors': authors,
                'branches': branches,
                'periods': periods,
                'revisions': revisions,
                'style': style,
                'query_filters': query_filters,
                'query_options': query_options,
                }

        # Javascripts
        add_script(req, 'revtree/js/suggest.js')
        add_script(req, 'revtree/js/revtree_query.js')
        add_script(req, 'revtree/js/revtree_folding.js')
        add_script(req, 'revtree/js/jquery_md5.js')
        add_script(req, 'revtree/js/XMLWriter-1.0.0-min.js')

        # JQuery §UI
        Chrome(self.env).add_jquery_ui(req)

        # Stylesheet
#        add_stylesheet(req, 'revtree/css/jquery.toolbar.css')
        add_stylesheet(req, 'revtree/css/font-awesome.css')
        add_stylesheet(req, 'revtree/css/revtree.css')

        # Date format
        date_hint = get_date_format_hint(req.lc_time)
        data.update({'date_hint': date_hint})

        # Scripts data
        add_script_data(req,
                        properties=properties,
                        revisions=revisions,
                        authors=authors,
                        periods=periods,
                        date_hint_len=len(date_hint),
                        date_hint_format=_('Format: %s') % date_hint
                        )

        # REMARK: add pseudo warning for front-end usage
        add_warning(req, " ")

        return 'revtree.html', data, None

    def _get_ui_periods(self):
        """Generates a list of periods"""
        periods = self.PERIODS
        days = sorted(periods.keys())
        return [dict(value=str(d), name=periods[d]) for d in days]

    def _get_ui_revisions(self, reverse=True):
        """Generates the list of displayable revisions"""
        repos = Repository(self.env)

        revmin = repos.get_oldest_rev()
        revmax = repos.get_youngest_rev()

        revisions = []
        for rev in xrange(int(revmax), int(revmin) - 1, -1):
#             if len(revisions) > 50:
#                 if rev % 100:
#                     continue
#             elif len(revisions) > 30:
#                 if rev % 20:
#                     continue
#             elif len(revisions) > 10:
#                 if rev % 10:
#                     continue

            revisions.append(rev)

        if revisions[-1] != int(revmin):
            revisions.append(int(revmin))

        return sorted(revisions, reverse=reverse)

    def _get_ui_authors(self):
        """Generates the list of displayable authors """
        repos = Repository(self.env)

        # Authors
        authors = sorted(repos.get_authors())
        authors.insert(0, '')

        return authors

    def cmp_func(self, a, b):
        b1, b2 = a[0], b[0]

        a_re = self.reg_expr.match(b1)
        b_re = self.reg_expr.match(b2)

        if b_re and a_re:
            a_int = int(a_re.group(1))
            b_int = int(b_re.group(1))

            if a_int != b_int:
                return cmp(a_int, b_int)
        return cmp(b1, b2)

    def _get_ui_branches(self, reverse=False):
        """Generates the list of displayable branches """
        repos = Repository(self.env)

        branches = repos.get_branch_names_with_prop()

        branches = sorted(branches, reverse=reverse, cmp=self.cmp_func)
        branches.insert(0, ('all', None))

        return branches
