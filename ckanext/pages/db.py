import datetime
import uuid
import json

import sqlalchemy as sa
from sqlalchemy.orm import class_mapper
try:
    from sqlalchemy.engine.result import RowProxy
except:
    from sqlalchemy.engine.base import RowProxy

pages_table = None
Page = None


def make_uuid():
    return unicode(uuid.uuid4())


def init_db(model):
    class _Page(model.DomainObject):

        @classmethod
        def get(cls, **kw):
            '''Finds a single entity in the register.'''
            query = model.Session.query(cls).autoflush(False)
            return query.filter_by(**kw).first()

        @classmethod
        def pages(cls, **kw):
            '''Finds a single entity in the register.'''
            order = kw.pop('order', False)
            order_publish_date = kw.pop('order_publish_date', False)
            order_publish_date_asc = kw.pop('order_publish_date_asc', False)
            order_side_menu_order = kw.pop('order_side_menu_order', False)

            query = model.Session.query(cls).autoflush(False)
            query = query.filter_by(**kw)
            if order:
                query = query.order_by(cls.order).filter(cls.order != '')
            elif order_publish_date:
                query = query.order_by(cls.publish_date.desc()).filter(cls.publish_date != None)
            elif order_publish_date_asc:
                query = query.order_by(cls.publish_date.asc()).filter(cls.publish_date != None)
            elif order_side_menu_order:
                query = query.order_by(cls.side_menu_order.asc())
            else:
                query = query.order_by(cls.created.desc())
            return query.all()

    global Page
    Page = _Page
    # We will just try to create the table.  If it already exists we get an
    # error but we can just skip it and carry on.
    sql = '''
                CREATE TABLE ckanext_pages (
                    id text NOT NULL,
                    title text,
                    name text,
                    content text,
                    lang text,
                    "order" text,
                    private boolean,
                    group_id text,
                    user_id text NOT NULL,
                    created timestamp without time zone,
                    modified timestamp without time zone
                );
    '''
    conn = model.Session.connection()
    try:
        conn.execute(sql)
    except sa.exc.ProgrammingError:
        pass
    model.Session.commit()

    sql_upgrade_01 = (
        "ALTER TABLE ckanext_pages add column publish_date timestamp;",
        "ALTER TABLE ckanext_pages add column page_type Text;",
        "UPDATE ckanext_pages set page_type = 'page';",
    )

    conn = model.Session.connection()
    try:
        for statement in sql_upgrade_01:
            conn.execute(statement)
    except sa.exc.ProgrammingError:
        pass
    model.Session.commit()

    sql_upgrade_02 = ('ALTER TABLE ckanext_pages add column extras Text;',
                      "UPDATE ckanext_pages set extras = '{}';")

    conn = model.Session.connection()
    try:
        for statement in sql_upgrade_02:
            conn.execute(statement)
    except sa.exc.ProgrammingError:
        pass
    model.Session.commit()

    sql_upgrade_07 = ('ALTER TABLE ckanext_pages add column parent_name Text;',
                      "UPDATE ckanext_pages set parent_name = '';")

    conn = model.Session.connection()
    try:
        for statement in sql_upgrade_07:
            conn.execute(statement)
    except sa.exc.ProgrammingError:
        pass
    model.Session.commit()

    sql_upgrade_08 = ('ALTER TABLE ckanext_pages add column side_menu_order Text;',
                      "UPDATE ckanext_pages set side_menu_order = '0';")

    conn = model.Session.connection()
    try:
        for statement in sql_upgrade_08:
            conn.execute(statement)
    except sa.exc.ProgrammingError:
        pass
    model.Session.commit()

    types = sa.types
    global pages_table
    pages_table = sa.Table('ckanext_pages', model.meta.metadata,
        sa.Column('id', types.UnicodeText, primary_key=True, default=make_uuid),
        sa.Column('title', types.UnicodeText, default=u''),
        sa.Column('name', types.UnicodeText, default=u''),
        sa.Column('content', types.UnicodeText, default=u''),
        sa.Column('lang', types.UnicodeText, default=u''),
        sa.Column('order', types.UnicodeText, default=u''),
        sa.Column('private',types.Boolean,default=True),
        sa.Column('group_id', types.UnicodeText, default=None),
        sa.Column('user_id', types.UnicodeText, default=u''),
        sa.Column('publish_date', types.DateTime),
        sa.Column('page_type', types.DateTime),
        sa.Column('created', types.DateTime, default=datetime.datetime.utcnow),
        sa.Column('modified', types.DateTime, default=datetime.datetime.utcnow),
        sa.Column('extras', types.UnicodeText, default=u'{}'),
        sa.Column('parent_name', types.UnicodeText, default=u''),
        sa.Column('side_menu_order', types.UnicodeText, default=u'0'),
        extend_existing=True
    )

    model.meta.mapper(
        Page,
        pages_table,
    )

    # Create the default about-page
    about_page = Page.get(name='about')
    if not about_page:
        about_page = Page()
        about_page.name = "about"
        about_page.title = "About"
        about_page.parent_name = ""
        about_page.private = False
        about_page.order = "4"
        about_page.side_menu_order = "0"
        model.Session.add(about_page)
        model.Session.commit()


def table_dictize(obj, context, **kw):
    '''Get any model object and represent it as a dict'''
    result_dict = {}

    if isinstance(obj, RowProxy):
        fields = obj.keys()
    else:
        ModelClass = obj.__class__
        table = class_mapper(ModelClass).mapped_table
        fields = [field.name for field in table.c]

    for field in fields:
        name = field
        if name in ('current', 'expired_timestamp', 'expired_id'):
            continue
        if name == 'continuity_id':
            continue
        value = getattr(obj, name)
        if name == 'extras' and value:
            result_dict.update(json.loads(value))
        elif value is None:
            result_dict[name] = value
        elif isinstance(value, dict):
            result_dict[name] = value
        elif isinstance(value, int):
            result_dict[name] = value
        elif isinstance(value, datetime.datetime):
            result_dict[name] = value.isoformat()
        elif isinstance(value, list):
            result_dict[name] = value
        else:
            result_dict[name] = unicode(value)

    result_dict.update(kw)

    ##HACK For optimisation to get metadata_modified created faster.

    context['metadata_modified'] = max(result_dict.get('revision_timestamp', ''),
                                       context.get('metadata_modified', ''))

    return result_dict
