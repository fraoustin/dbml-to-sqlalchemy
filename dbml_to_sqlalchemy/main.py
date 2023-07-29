from re import sub, search
import enum
from dbml_to_sqlalchemy import mymodel

from pydbml import PyDBML
from sqlalchemy import PrimaryKeyConstraint, UniqueConstraint, ForeignKeyConstraint
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql import expression
from sqlalchemy.orm import relationship
import sqlalchemy.types
from sqlalchemy import Enum
import sqlalchemy.sql.sqltypes
types = {typ.lower(): getattr(sqlalchemy.types, typ) for typ in dir(sqlalchemy.types) if typ in dir(sqlalchemy.sql.sqltypes) and '_' not in typ}

__version__ = '0.9.1'


def toCamelCase(st):
    st = sub('[^a-zA-Z0-9 \n]', '', st.replace('.', ' '))
    return sub(r"(_|-)", " ", st).title().replace(" ", "")


def toColumnCase(st):
    st = sub('[^a-zA-Z0-9 _\n]', '', st.replace('.', ' '))
    return st.lower().replace(" ", "_")


def toTableCase(st):
    return st.lower().replace(" ", "_")


def getType(st, default=sqlalchemy.types.String):
    if st.__class__.__name__ == 'Enum':
        return Enum
    return types.get(st.split('(')[0].lower(), default)


def getTypeParams(st):
    try:
        if st.__class__.__name__ == 'Enum':
            return [enum.Enum(st.name, [item.name for item in st.items]), ], {"create_constraint": True}
        return [param.isnumeric() and int(param) or param for param in search(r'\((.*)\)', st).group(0)[1:-1].split(',')], {}
    except Exception:
        return [], {}


def getServerDefault(val):
    if isinstance(val, bool):
        if bool is False:
            return expression.false()
        return expression.true()
    if val is None:
        return val
    return str(val)


def spec_many(newt, name):
    @property
    def decorator(f):
        return [getattr(elt, name) for elt in getattr(f, newt)]
    return decorator


def spec_doc(col):
    doc = []
    if col.pk:
        doc.append('primary key')
    if col.autoinc:
        doc.append('autoincrement')
    if col.not_null:
        doc.append('not null')
    if col.unique:
        doc.append('unique')
    if col.default is not None:
        doc.append('default: %s' % col.default)
    if len(doc) > 0:
        return '(%s)' % ', '.join(doc)
    return ''


def createModel(table, *cls, module=mymodel):
    if len(table.note.text) == 0:
        table.note.text = '%s Table' % toCamelCase(table.name)
    cols = {col.name: Column(toColumnCase(col.name), getType(col.type)(*getTypeParams(col.type)[0], **getTypeParams(col.type)[1]), primary_key=col.pk, autoincrement=col.autoinc, nullable=not (col.not_null), default=col.default, server_default=getServerDefault(col.default), unique=col.unique, comment=col.note) for col in table.columns}
    tableArgs = []
    for index in [index for index in table.indexes if index.pk is True]:
        tableArgs.append(PrimaryKeyConstraint(*[cols[col.name] for col in index.subjects]))
    for index in [index for index in table.indexes if index.unique is True]:
        subargs = {}
        if index.name is not None:
            subargs = {'name': index.name}
        tableArgs.append(UniqueConstraint(*[cols[col.name] for col in index.subjects], **subargs))
    SomeClass = type(toCamelCase(table.name), cls, {
        "__tablename__": toTableCase(table.name),
        "__table_args__": tuple(tableArgs),
        "__doc__": "%s\n\n%s" % (table.note, '\n'.join([":param %s: %s %s\n:type %s: %s" % (col.name, col.note, spec_doc(col), col.name, col.type) for col in table.columns])),
        **cols
    })
    setattr(module, toCamelCase(table.name), SomeClass)
    for ref in [ref for ref in table.database.refs if (ref.table1 == table or ref.table2 == table) and getattr(module, toCamelCase(ref.col2[0].table.name), None) is not None and getattr(module, toCamelCase(ref.col1[0].table.name), None) is not None]:
        class1 = getattr(module, toCamelCase(ref.table1.name))
        class2 = getattr(module, toCamelCase(ref.table2.name))
        if ref.type in ('<'):
            class2.__table_args__ = class2.__table_args__ + (ForeignKeyConstraint([getattr(class2, col.name) for col in ref.col2], [getattr(class1, col.name) for col in ref.col1], name=ref.name), )
        if ref.type in ('>', '-'):
            class1.__table_args__ = class1.__table_args__ + (ForeignKeyConstraint([getattr(class1, col.name) for col in ref.col1], [getattr(class2, col.name) for col in ref.col2], name=ref.name), )
        if ref.type == '<':
            setattr(class1, "%ss" % class2.__name__.lower(), relationship(class2.__name__, back_populates=class1.__name__.lower()))
            class1.__doc__ = class1.__doc__ + "\n:param %ss:\n:type %ss: relationship(%s)" % (class2.__name__.lower(), class2.__name__.lower(), class2.__name__)
            setattr(class2, class1.__name__.lower(), relationship(class1.__name__, back_populates="%ss" % class2.__name__.lower()))
            class2.__doc__ = class2.__doc__ + "\n:param %s :\n:type %s: %s" % (class1.__name__.lower(), class1.__name__.lower(), class1.__name__)
        elif ref.type == '>':
            setattr(class1, class2.__name__.lower(), relationship(class2.__name__, back_populates="%ss" % class1.__name__.lower()))
            class1.__doc__ = class1.__doc__ + "\n:param %s:\n:type %s: %s" % (class2.__name__.lower(), class2.__name__.lower(), class2.__name__)
            setattr(class2, "%ss" % class1.__name__.lower(), relationship(class1.__name__, back_populates=class2.__name__.lower()))
            class2.__doc__ = class2.__doc__ + "\n:param %ss:\n:type %ss: relationship(%s):" % (class1.__name__.lower(), class1.__name__.lower(), class1.__name__)
        elif ref.type == '-':
            setattr(class1, class2.__name__.lower(), relationship(class2.__name__, uselist=False, back_populates=class1.__name__.lower()))
            setattr(class2, class1.__name__.lower(), relationship(class1.__name__, uselist=False, back_populates=class2.__name__.lower()))
        if ref.type == '<>':
            newt_name = "%s_%s" % (ref.table1.name, ref.table2.name)
            newt_col1 = "\n".join(["%s_%s %s" % (col.table.name, col.name, col.type) for col in ref.col1])
            newt_col2 = "\n".join(["%s_%s %s" % (col.table.name, col.name, col.type) for col in ref.col2])
            newt_pk = "%s, %s" % ("\n".join(["%s_%s" % (col.table.name, col.name) for col in ref.col1]), "\n".join(["%s_%s" % (col.table.name, col.name) for col in ref.col2]))
            new_table = "Table %s\n{\n%s\n%s\nindexes {\n(%s) [pk]\n}\n}" % (newt_name, newt_col1, newt_col2, newt_pk)
            newt = createModel(PyDBML(new_table).tables[0], *cls, module=module)
            newt.__table_args__ = newt.__table_args__ + (ForeignKeyConstraint([getattr(newt, "%s_%s" % (col.table.name, col.name)) for col in ref.col1], [getattr(class1, col.name) for col in ref.col1]), )
            newt.__table_args__ = newt.__table_args__ + (ForeignKeyConstraint([getattr(newt, "%s_%s" % (col.table.name, col.name)) for col in ref.col2], [getattr(class2, col.name) for col in ref.col2]), )
            setattr(class1, "%ss" % newt.__name__.lower(), relationship(newt.__name__, back_populates=class1.__name__.lower()))
            class1.__doc__ = class1.__doc__ + "\n:param %ss:\n:type %ss: relationship(%s)" % (newt.__name__.lower(), newt.__name__.lower(), newt.__name__)
            setattr(newt, class1.__name__.lower(), relationship(class1.__name__, back_populates="%ss" % newt.__name__.lower()))
            newt.__doc__ = newt.__doc__ + "\n:param %s:\n:type %s: %s" % (class1.__name__.lower(), class1.__name__.lower(), class1.__name__)
            setattr(class2, "%ss" % newt.__name__.lower(), relationship(newt.__name__, back_populates=class2.__name__.lower()))
            class2.__doc__ = class2.__doc__ + "\n:param %ss:\n:type %ss: relationship(%s):" % (newt.__name__.lower(), newt.__name__.lower(), newt.__name__)
            setattr(newt, class2.__name__.lower(), relationship(class2.__name__, back_populates="%ss" % newt.__name__.lower()))
            newt.__doc__ = newt.__doc__ + "\n:param %s:\n:type %s: %s:" % (class2.__name__.lower(), class2.__name__.lower(), class2.__name__)
            setattr(class1, "%ss" % class2.__name__.lower(), spec_many("%ss" % newt.__name__.lower(), class2.__name__.lower()))
            class1.__doc__ = class1.__doc__ + "\n:param %ss:\n:type %ss: relationship(%s)" % (class2.__name__.lower(), class2.__name__.lower(), class2.__name__)
            setattr(class2, "%ss" % class1.__name__.lower(), spec_many("%ss" % newt.__name__.lower(), class1.__name__.lower()))
            class2.__doc__ = class2.__doc__ + "\n:param %ss:\n:type %ss: relationship(%s)" % (class1.__name__.lower(), class1.__name__.lower(), class1.__name__)
            setattr(module, newt.__name__, newt)
    return getattr(module, toCamelCase(table.name))
