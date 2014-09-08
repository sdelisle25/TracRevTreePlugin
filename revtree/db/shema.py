# -*- coding: utf-8 -*-

from trac.db import Table, Column, Index

# Database version identifier. Used for automatic upgrades.
db_version = 1

schema = [
    Table('revtree_brings')[
        Column('branch'),
        Column('revision', type='int'),
        Column('bring')],

    Table('revtree_delivers')[
        Column('branch'),
        Column('revision', type='int'),
        Column('deliver')],

    Table('revtree_tags')[
        Column('name'),
        Column('prettyname'),
        Column('tag_revision', type='int'),
        Column('branch'),
        Column('revision', type='int')],

    # Revtree table
    Table('revtree_revisions')[
        Column('revision', type='int'),
        Column('branch'),
        Column('branch_name'),
        Column('author'),
        Column('date', type='int64'),
        Column('last'),
        Column('clone')],

    Table('revtree_branches')[
        Column('branch'),
        Column('name'),
        Column('date', type='int64'),
        Column('firstrev', type='int'),
        Column('lastrev', type='int'),
        Column('revisions'), # comma-separated revisions
        Column('srcpath'),
        Column('srcrev', type='int'),
        Column('terminalrev', type='int'),
        Index(['branch'])
        ],
]
