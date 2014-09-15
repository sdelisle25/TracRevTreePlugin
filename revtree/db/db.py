# -*- coding: utf-8 -*-

from revtree.containers import BranchEntry
from revtree.db.shema import db_version, schema
from revtree.model import Repository
from trac.util.text import to_unicode
from trac.core import Component, implements, TracError
from trac.db import DatabaseManager
from trac.db.api import _parse_db_str
from trac.env import IEnvironmentSetupParticipant
from trac.util.datefmt import to_timestamp
import traceback


def _db_to_version(name):
    return int(name.lstrip('db'))


class DBMixing(object):
    def droptables(self):
        self.env.log.debug('Drop Revtree tables')

        scheme, _ = _parse_db_str(DatabaseManager(self.env).connection_uri)
        if scheme == 'sqlite':
            table_sql = "SELECT name FROM sqlite_master WHERE type='table' " \
                        "AND name LIKE 'revtree_%'"
        elif scheme == 'postgres':
            table_sql = "SELECT tablename FROM pg_tables WHERE schemaname='public' " \
                        "AND tablename LIKE 'revtree_%'"
        else:
            raise TracError('DB scheme "%s" is not managed' % scheme)

        # Delete scheme revision
        self.env.db_transaction("DELETE FROM system WHERE name=%s",
                                (self.plugin_name + '_version', ))

        # Drop tables
        rows = self.env.db_query(table_sql)
        for tlb, in rows:
            try:
                self.env.db_transaction("DROP TABLE %s" % tlb)
            except Exception as excpt:
                raise TracError("DB Revtree tables can not be dropped " \
                                "exception='%s" % str(excpt))

    def upgrade_environment(self, db):
        # Drop tables
        self.droptables()

        installed = self.get_installed_version(db)

        # No tables
        if installed is None:
            self.env.log.info('Installing Revtree plugin schema %s' % db_version)
            db_connector, _ = DatabaseManager(self.env)._get_connector()
            db = self._get_db(db)
            cursor = db.cursor()

            for table in schema:
                for stmt in db_connector.to_sql(table):
                    cursor.execute(stmt)

            self.set_installed_version(db, db_version)
            self.env.log.info('Installation of %s successful.' % db_version)
            db.commit()
            return

        # Upgrade tables schema
        self.env.log.debug('Upgrading schema for "%s".' % type(self).__name__)
        for version, fn in self.get_schema_functions():
            if version > installed:
                self.env.log.info('Upgrading TracForm plugin schema to %s' % version)
                self.env.log.info('- %s: %s' % (fn.__name__, fn.__doc__))
                db = self._get_db(db)
                cursor = db.cursor()
                fn(self.env, cursor)
                self.set_installed_version(db, version)
                installed = version
                self.env.log.info('Upgrade to %s successful.' % version)

    def get_installed_version(self, db):
        version = self.get_system_value(db, self.plugin_name + '_version', -1)
        return int(version) if version else None

    def get_schema_functions(self, prefix='db'):
        fns = []
        for name in self.__dict__:
            if name.startswith(prefix):
                fns.append((_db_to_version(name), getattr(self, name)))
        for cls in type(self).__mro__:
            for name in cls.__dict__:
                if name.startswith(prefix):
                    fns.append((_db_to_version(name), getattr(self, name)))
        fns.sort()
        return tuple(fns)

    def set_installed_version(self, db, version):
        self.set_system_value(db, self.plugin_name + '_version', version)

    def get_system_value(self, db, key, default=None):
        db = self._get_db(db)
        cursor = db.cursor()
        cursor.execute("SELECT value FROM system WHERE name=%s", (key,))
        row = cursor.fetchone()
        return row and row[0]

    def set_system_value(self, db, key, value):
        """Atomic UPSERT db transaction to save TracForms version."""
        db = self._get_db(db)
        cursor = db.cursor()
        cursor.execute(
                "UPDATE system SET value=%s WHERE name=%s", (value, key))
        cursor.execute("SELECT value FROM system WHERE name=%s", (key,))
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO system(name, value) VALUES(%s, %s)", (key, value))

    # Low level database connection management
    def _get_db(self, db=None):
        return db or self.env.get_db_cnx()


class DBUpdater(DBMixing):
    plugin_name = 'revtree'

    def __init__(self, env, bcre):
        super(DBUpdater, self).__init__()
        self.env = env
        self.bcre = bcre
        self.repos = Repository(env)

    def sync(self, revrange=None):
        if not revrange:
            return self._sync_revrange(revrange=None)

        # Get RevTree table revisions
        rows = self.env.db_query("SELECT revision FROM revtree_revisions")
        revisions = [int(rev) for rev, in rows]

        # REMARK: tag revision not in revtree_revisions table so add them
        rows = self.env.db_query("SELECT tag_revision FROM revtree_tags")
        for rev, in rows:
            revisions.append(int(rev))
        revisions.sort(reverse=False)

        # Theorical revision range
        revisions_range = set()
        for rev in xrange(revisions[0], revisions[-1]):
            revisions_range.add(rev)

        # Use set for better performance
        revisions = set(revisions)
        missing_revisions = list(revisions_range.difference(revisions))
        missing_revisions.sort(reverse=False)

        revrange = list(revrange)

        missing_revisions.append(revrange[1])

        # Synchronize with missing revisions
        if missing_revisions and missing_revisions[0] < revrange[0]:
            revrange[0] = missing_revisions[0]

        for rev in missing_revisions:
            self._sync_revrange((rev, rev))

    def _sync_revrange(self, revrange):
        # Build informations from repository
        self.repos = Repository(self.env)
        self.repos.build(self.bcre, revrange=revrange)

        self.env.log.debug("Synchronize for revision range='%s'" % \
                            str(revrange))

        try:
            # Build tags table
            tags = self.repos.tags()
            for tag in tags.values():
                # Verify tag do not exist
                rows = self.env.db_query("SELECT * FROM revtree_tags "
                                         "WHERE name=%s", (tag.name,))
                if rows:
                    self.env.log.debug("Tag name='%s' already exist", tag.name)
                    continue

                with self.env.db_transaction as db:
                    args = (to_unicode(tag.name),
                            to_unicode(tag.prettyname),
                            tag.rev,
                            to_unicode(tag.clone[1]),
                            tag.clone[0])
                    db("""INSERT INTO revtree_tags (name, prettyname, tag_revision, branch, revision)
                          VALUES(%s, %s, %s, %s, %s)""", args)

            # Build revisions table
            for rev, vc in self.repos.changesets().iteritems():
                if not vc.branchname:
                    continue

                # Verify revision do not exist
                rows = self.env.db_query("SELECT * FROM revtree_revisions "
                                         "WHERE revision=%s", (rev,))
                if rows:
                    self.env.log.debug("Revision='%s' already exist", rev)
                    continue

                branch_name = to_unicode(vc.branchname)
                pretty_name = to_unicode(vc.prettyname)
                author = to_unicode(vc.changeset.author)

                with self.env.db_transaction as db:
                    self.env.log.debug("Insert revision='%s'", rev)

                    # Brings information
                    bring = vc.prop('rth:bring')
                    if bring:
                        args = (branch_name, rev, bring)

                        db("INSERT INTO revtree_brings (branch, revision," \
                           " bring) VALUES(%s, %s, %s)", args)

                    # Delivers information
                    deliver = vc.prop('rth:deliver')
                    if deliver:
                        args = (branch_name, rev, deliver)
                        db("""INSERT INTO revtree_delivers (branch, revision, deliver)
                           VALUES(%s, %s, %s)""", args)

                    # Revision information
                    args = (int(rev),
                            branch_name,
                            pretty_name,
                            author,
                            to_timestamp(vc.date),
                            str(vc.last),
                            str(vc.clone))
                    db("""INSERT INTO revtree_revisions (revision, branch, branch_name, author, date, last, clone)
                       VALUES(%s, %s, %s, %s, %s, %s, %s)""", args)

                    self.update_branch(vc, db)
        except:
            self.env.log.error('revtree update error %s' %
                               traceback.format_exc())
            raise

    def resync_rev(self, rev):
        # Build informations from repository
        self.repos = Repository(self.env)
        self.repos.build(self.bcre, revrange=[rev, rev])

        self.env.log.debug("Synchronize for revision range='%s'" % \
                            str([rev, rev]))

        try:
            # Build revisions table
            for rev, vc in self.repos.changesets().iteritems():
                if not vc.branchname:
                    continue

                # Verify revision do not exist
                rows = self.env.db_query("SELECT * FROM revtree_revisions "
                                         "WHERE revision=%s", (rev,))
                if not rows:
                    self.env.log.debug("Revision='%s' do not exist", rev)
                    continue

                branch_name = to_unicode(vc.branchname)
                pretty_name = to_unicode(vc.prettyname)
                author = to_unicode(vc.changeset.author)

                with self.env.db_transaction as db:
                    self.env.log.debug("Update revision='%s'", rev)

                    # Brings information
                    bring = vc.prop('rth:bring')
                    if bring:
                        # Verify revision bring do not exist
                        rows = self.env.db_query("SELECT * FROM revtree_brings "
                                                 "WHERE revision=%s", (rev,))
                        if not rows:
                            args = (branch_name, rev, bring)

                            db("INSERT INTO revtree_brings (branch, revision," \
                               " bring) VALUES(%s, %s, %s)", args)
                        else:
                            db("UPDATE revtree_brings SET bring=%%s " \
                               " WHERE (branch='%s' AND revision=%s)" % \
                               (branch_name, rev), (bring,))
                    else:
                        db("DELETE from revtree_brings " \
                           " WHERE (branch='%s' AND revision=%s)" %
                           (branch_name, rev))

                    # Delivers information
                    deliver = vc.prop('rth:deliver')
                    if deliver:
                        # Verify revision deliver do not exist
                        rows = self.env.db_query("SELECT * FROM revtree_delivers "
                                                 "WHERE revision=%s", (rev,))
                        if not rows:
                            args = (branch_name, rev, deliver)
                            db("INSERT INTO revtree_delivers (branch, " \
                               "revision, deliver) VALUES(%s, %s, %s)", args)
                        else:
                            db("UPDATE revtree_delivers SET deliver=%%s " \
                               " WHERE (branch='%s' AND revision=%s)" % \
                               (branch_name, rev), (deliver,))
                    else:
                        db("DELETE from revtree_delivers" \
                           " WHERE (branch='%s' AND revision=%s)" % \
                           (branch_name, rev))

                    # Revision information
                    args = (int(rev),
                            branch_name,
                            pretty_name,
                            author,
                            to_timestamp(vc.date),
                            str(vc.last),
                            str(vc.clone))
                    db("UPDATE revtree_revisions SET revision=%%s, branch=%%s," \
                       " branch_name=%%s, author=%%s, date=%%s, " \
                       "last=%%s, clone=%%s " \
                       "WHERE (branch='%s' AND revision=%s)" % \
                       (branch_name, rev), args)
        except:
            self.env.log.error('revtree update error %s' %
                               traceback.format_exc())
            raise

    def update_branch(self, vc, db):
        brc = BranchEntry()

        brc_name = to_unicode(vc.branchname)
        pretty_name = to_unicode(vc.prettyname)

        row = self.env.db_query("SELECT * from revtree_branches WHERE (branch=%s" \
                                "AND terminalrev IS NULL)", (brc_name,))
        if not row:
            brc.branch = brc_name
            brc.name = pretty_name

            brc.firstrev = vc.rev
            brc.date = to_timestamp(vc.date)
            sql = "INSERT INTO revtree_branches VALUES (%s)" % brc.sql_fmt()
        else:
            brc.set(*row[0])
            # REMARK: %%s mandatory to get %s in final string
            fmt = ', '.join('%s = %%s' % n for n in brc._field_names)
            sql = "UPDATE revtree_branches SET %s WHERE (branch='%s' AND " \
                  " (terminalrev IS NULL))" % (fmt, brc_name)

        # Update fields
        brc.lastrev = vc.rev
        brc.revisions = ','.join([brc.revisions, str(vc.rev)]) \
                        if brc.revisions else '%s' % str(vc.rev)

        if vc.last:
            brc.terminalrev = vc.rev

        if vc.clone:
            brc.srcrev = int(vc.clone[0])
            brc.srcpath = vc.clone[1]

        args = tuple(brc.sql_data())
        db(sql, args)


class DBComponent(Component, DBMixing):
    """Provides RevTree db schema management methods."""

    implements(IEnvironmentSetupParticipant)

    plugin_name = 'revtree'

    # IEnvironmentSetupParticipant methods

    def environment_created(self):
        pass

    def environment_needs_upgrade(self, db):
        installed = self.get_installed_version(db)
        if not installed:
            return True

        for version, fn in self.get_schema_functions():
            if version > installed:
                self.env.log.debug(
                    '"%s" requires a schema upgrade.' % type(self).__name__)
                return True
        else:
            self.env.log.debug(
                '"%s" does not need a schema upgrade.' % type(self).__name__)
            return False

