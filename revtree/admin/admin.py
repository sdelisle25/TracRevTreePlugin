# -*- coding: utf-8 -*-

from revtree.db.db import DBUpdater
from trac.admin.api import IAdminCommandProvider
from trac.config import Option
from trac.core import Component, implements
import re


class RevTreeAdmin(Component):
    """trac-admin command provider for version control administration."""

    autoload = True

    # Configuration Options
    branchre = Option('revtree', 'branch_re',
                      r'^(?:(?P<branch>trunk|(?:branches|sandboxes|vendor)/'
                      r'(?P<branchname>[^/]+))|'
                      r'(?P<tag>tags/(?P<tagname>[^/]+)))(?:/(?P<path>.*))?$',
        doc="""Regular expression to extract branches from paths""")

    implements(IAdminCommandProvider)

    def __init__(self, *args, **kwargs):
        super(RevTreeAdmin, self).__init__(*args, **kwargs)

        self.env.log.debug('Revtree RE: %s' % self.branchre)
        self._bcre = re.compile(self.branchre)

        self._db_updater = DBUpdater(self.env, self._bcre)

    # IAdminCommandProvider methods
    def get_admin_commands(self):
        yield ('revtree resync', '',
               """Resynchronize revtree tables""",
               None, self._do_resync)

        yield ('revtree droptables', '', """Drop revtree tables""",
               None, self._do_drop_tables)

    def _do_resync(self):
        self._db_updater.sync(revrange=None)

    def _do_drop_tables(self):
        self._db_updater.droptables()
