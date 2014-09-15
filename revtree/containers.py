# -*- coding: utf-8 -*-
from trac.util.text import to_unicode


class StructContainer(object):

    """ Data container, C structure style fields are define through _field_names
    class attribute, in init method fields are inited with corresponding kwargs
    value if any else None value is affected to the field """
    _field_names = []

    def __init__(self, **kwargs):
        """ Init method. """
        super(StructContainer, self).__init__()
        for k in self._field_names:
            self.__dict__[k] = kwargs.get(k, None)

    def update(self, **kwargs):
        """
        Update fields matching in kwargs and object fields, do not add
        undefined _arg_named field in kwargs
        """
        for key in self._field_names:
            if key in kwargs:
                self.__dict__[key] = kwargs.get(key)

    def __setattr__(self, name, value):
        if name not in self._field_names:
            raise Exception("Attribute='%s' do not exist" % name)
        self.__dict__[name] = value
        return value

    def sql_fmt(self):
        return ", ".join(['%s' for _ in self._field_names])

    def sql_data(self):
        data = []
        for name in self._field_names:
            if self.__dict__[name] is None:
                data.append(None)
            else:
                data.append(to_unicode(self.__dict__[name]))
        return data

    def set(self, *args):
        for n, v in zip(self._field_names, args):
#             if isinstance(v, str):
#                 v = to_unicode(v)  # Convert to unicode object
            self.__dict__[n] = v
        return self

    def get_revisions(self):
        return sorted([int(r) for r in self.revisions.split(',')],
                      reverse=True)


class RevisionEntry(StructContainer):
    _field_names = ['revision', 'branch', 'branch_name', 'author', 'date',
                    'last', 'clone']


class BranchEntry(StructContainer):
    _field_names = ['branch', 'name', 'date', 'firstrev', 'lastrev',
                    'revisions', 'srcpath', 'srcrev', 'terminalrev']


class TagEntry(StructContainer):
    _field_names = ['name', 'prettyname', 'tag_revision', 'branch', 'revision']


class DeliverEntry(StructContainer):
    _field_names = ['branch', 'revision', 'deliver']

    def get_revisions(self):
        return sorted([int(r) for r in self.deliver.split(',')], reverse=True)


class BringEntry(StructContainer):
    _field_names = ['branch', 'revision', 'bring']

    def get_revisions(self):
        return sorted([int(r) for r in self.bring.split(',')], reverse=True)
