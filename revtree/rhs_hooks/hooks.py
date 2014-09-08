"""
annotes and closes tickets based on an SVN commit message;
port of http://trac.edgewall.org/browser/trunk/contrib/trac-post-commit-hook
"""

from repository_hook_system.interface import IRepositoryHookSubscriber
from revtree.db.db import DBUpdater
from trac.core import Component, implements
from trac.config import Option
import re

class PostCommit(Component):

    """Register to repository hook system the post-commit hook, invoked to
    populate new revision information into revtree tables."""

    # Configuration Options
    branchre = Option('revtree', 'branch_re',
                      r'^(?:(?P<branch>trunk|(?:branches|sandboxes|vendor)/'
                      r'(?P<branchname>[^/]+))|'
                      r'(?P<tag>tags/(?P<tagname>[^/]+)))(?:/(?P<path>.*))?$',
        doc="""Regular expression to extract branches from paths""")

    def __init__(self, *args, **kwargs):
        super(PostCommit, self).__init__(*args, **kwargs)

        self.env.log.debug('Revtree RE: %s' % self.branchre)
        self._bcre = re.compile(self.branchre)

    implements(IRepositoryHookSubscriber)

    def is_available(self, repository, hookname):
        """
        Verify if hook name is valid.

        :param repository: repository type
        :param hookname: hook name
        """
        return (hookname == 'post-commit')

    def invoke(self, revision=None, changeset=None, **kwargs):
        """
        Invoke by hook system on post_commit operation

        :param project: Project path, Trac env project
        :param repository: repository path
        :param user: author of the modification
        :param revision: revision for post_commit
        """

        if changeset:
            revision = changeset.rev

        self.env.log.debug("Resync revtree tables for")
        self._do_sync(revision)

    def _do_sync(self, rev):
        db_updater = DBUpdater(self.env, self._bcre)

        db_updater.sync(revrange=(int(rev), int(rev)))

        self.env.log.debug("Update revtree tables for revision='%s'" % rev)


class PostRevPropChange(Component):

    branchre = Option('revtree', 'branch_re',
                      r'^(?:(?P<branch>trunk|(?:branches|sandboxes|vendor)/'
                      r'(?P<branchname>[^/]+))|'
                      r'(?P<tag>tags/(?P<tagname>[^/]+)))(?:/(?P<path>.*))?$',
        doc="""Regular expression to extract branches from paths""")

    implements(IRepositoryHookSubscriber)

    def __init__(self, *args, **kwargs):
        super(PostRevPropChange, self).__init__(*args, **kwargs)

        self.env.log.debug('Revtree RE: %s' % self.branchre)
        self._bcre = re.compile(self.branchre)

    def is_available(self, repository, hookname):
        """
        Verify if hook name is valid.

        :param repository: repository type
        :param hookname: hook name
        """
        return (hookname == 'post-revprop-change')

    def invoke(self, project, revision, propname,
               action, user, repository, **kwargs):

        db_updater = DBUpdater(self.env, self._bcre)

        db_updater.resync_rev(int(revision))
