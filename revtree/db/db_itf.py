# -*- coding: utf-8 -*-

from revtree.containers import (BranchEntry, BringEntry, TagEntry,
                                RevisionEntry, DeliverEntry)


class DBInterface(object):

    def __init__(self, env):
        super(DBInterface, self).__init__()
        self.env = env

    def get_brings(self, branch_name):
        rows = self.env.db_query("SELECT * FROM revtree_brings " \
                                 "WHERE branch='%s'" % branch_name)
        for row in rows:
            # Branch entry
            brc = BringEntry()
            brc.set(*row)
            yield brc

    def get_tags(self):
        rows = self.env.db_query("SELECT * FROM revtree_tags")
        for row in rows:
            # Branch entry
            brc = TagEntry()
            brc.set(*row)
            yield brc

    def get_branch_names(self):
        return [b for b, in
                self.env.db_query("SELECT DISTINCT branch FROM " \
                                  "revtree_branches")]

    def get_branch_names_with_prop(self, prop="terminalrev"):
        return [b for b in
                self.env.db_query("SELECT branch, %s FROM " \
                                  "revtree_branches" % prop)]

    def get_branch(self, name, rev=None):
        rows = self.env.db_query("SELECT * FROM revtree_branches " \
                                 "WHERE branch='%s'" % name)

        branches = []
        for row in rows:
            brc = BranchEntry()
            brc.set(*row)
            if rev and rev in brc.get_revisions():
                return [brc, ]
            branches.append(brc)
        return branches

    def get_authors(self):
        return [a for a, in
                self.env.db_query("SELECT DISTINCT author FROM " \
                                  "revtree_revisions")]

    def get_revisions(self):
        with self.env.db_query as db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM revtree_revisions " \
                           "ORDER BY revision DESC")
            row = cursor.fetchone()
            while(row):
                yield RevisionEntry().set(*row)
                row = cursor.fetchone()

    def get_branches(self):
        rows = self.env.db_query("SELECT * FROM revtree_branches")
        for row in rows:
            # Branch entry
            brc = BranchEntry()
            brc.set(*row)
            yield brc

    def get_delivers(self, branch_name):
        rows = self.env.db_query("SELECT * FROM revtree_delivers "\
                                 " WHERE branch='%s'" % branch_name)
        for row in rows:
            # Branch entry
            brc = DeliverEntry()
            brc.set(*row)
            yield brc
