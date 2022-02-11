import datetime
import uuid
import json

from six import text_type
import sqlalchemy as sa
from sqlalchemy.orm import class_mapper
from migrate.versioning.schema import Table, Column

try:
    from sqlalchemy.engine.result import RowProxy
except ImportError:
    from sqlalchemy.engine.base import RowProxy
from ckan import model
from ckan.model.domain_object import DomainObject

pages_table = None


def make_uuid():
    return text_type(uuid.uuid4())


def init_db():
    print("#"*15)
    print("#   init db   #")
    print("#"*15)
    if pages_table is None:
        print("--> define_tables")
        define_tables()

    if not pages_table.exists():
        print("--> pages_table.create")
        pages_table.create()
    else:
        print("--> pages_table.exported_columns")
        pages_columns = pages_table.exported_columns if hasattr(pages_table, 'exported_columns') \
            else pages_table.columns
        if 'side_menu_grouping' not in [c.name for c in pages_columns]:
            print('side_menu_grouping')
            pages_table.append_column(sa.Column('side_menu_grouping', sa.types.UnicodeText, default=None))
            table = Table('ckanext_pages', model.meta.metadata)
            col = Column('side_menu_grouping', sa.types.UnicodeText, default=None)
            col.create(table)


class Page(DomainObject):

    @classmethod
    def get(cls, **kw):
        """Finds a single entity in the register."""
        query = model.Session.query(cls).autoflush(False)
        return query.filter_by(**kw).first()

    @classmethod
    def pages(cls, **kw):
        """Finds a single entity in the register."""
        order = kw.pop('order', False)
        order_publish_date = kw.pop('order_publish_date', False)
        order_publish_date_asc = kw.pop('order_publish_date_asc', False)
        order_side_menu_order = kw.pop('order_side_menu_order', False)

        query = model.Session.query(cls).autoflush(False)
        query = query.filter_by(**kw)
        if order:
            query = query.order_by(sa.cast(cls.order, sa.Integer)).filter(cls.order != '')
        elif order_publish_date:
            query = query.order_by(cls.publish_date.desc()).filter(cls.publish_date is not None)  # noqa: E711
        elif order_publish_date_asc:
            query = query.order_by(cls.publish_date.asc()).filter(cls.publish_date is not None)
        elif order_side_menu_order:
            query = query.order_by(cls.side_menu_order.asc())
        else:
            query = query.order_by(cls.created.desc())
        return query.all()


def define_tables():
    types = sa.types
    global pages_table
    pages_table = sa.Table('ckanext_pages', model.meta.metadata,
                           sa.Column('id', types.UnicodeText, primary_key=True, default=make_uuid),
                           sa.Column('title', types.UnicodeText, default=u''),
                           sa.Column('title_nl', types.UnicodeText, default=u''),
                           sa.Column('title_fr', types.UnicodeText, default=u''),
                           sa.Column('title_de', types.UnicodeText, default=u''),
                           sa.Column('name', types.UnicodeText, default=u''),
                           sa.Column('content', types.UnicodeText, default=u''),
                           sa.Column('content_nl', types.UnicodeText, default=u''),
                           sa.Column('content_fr', types.UnicodeText, default=u''),
                           sa.Column('content_de', types.UnicodeText, default=u''),
                           sa.Column('lang', types.UnicodeText, default=u''),
                           sa.Column('order', types.UnicodeText, default=u''),
                           sa.Column('private', types.Boolean, default=True),
                           sa.Column('group_id', types.UnicodeText, default=None),
                           sa.Column('user_id', types.UnicodeText, default=u''),
                           sa.Column('publish_date', types.DateTime),
                           sa.Column('page_type', types.UnicodeText),
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

    # Create the default news-page
    news_page = Page.get(name='news')
    if not news_page:
        news_page = Page()
        news_page.name = "news"
        news_page.title = "News"
        news_page.parent_name = ""
        news_page.private = False
        news_page.order = "3"
        news_page.side_menu_order = "0"
        model.Session.add(news_page)
        model.Session.commit()


def table_dictize(obj, context, **kw):
    """Get any model object and represent it as a dict"""
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
        value = getattr(obj, name) if hasattr(obj, name) else None
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
            result_dict[name] = text_type(value)

    result_dict.update(kw)

    # HACK For optimisation to get metadata_modified created faster.

    context['metadata_modified'] = max(result_dict.get('revision_timestamp', ''),
                                       context.get('metadata_modified', ''))

    return result_dict
