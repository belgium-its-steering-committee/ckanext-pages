import cgi
import logging
import urllib
from ckan.common import config
import ckan.plugins.toolkit as toolkit
import ckan.plugins as p
import ckan.lib.helpers as h
import actions
import auth

ignore_missing = toolkit.get_validator('ignore_missing')

if toolkit.check_ckan_version(min_version='2.8'):
    from ckan.lib.plugins import DefaultTranslation


    class PagesPluginBase(p.SingletonPlugin, DefaultTranslation):
        p.implements(p.ITranslation, inherit=True)
else:
    class PagesPluginBase(p.SingletonPlugin):
        pass

log = logging.getLogger(__name__)


def build_pages_nav_main(*args):
    about_menu = toolkit.asbool(config.get('ckanext.pages.about_menu', False))
    group_menu = toolkit.asbool(config.get('ckanext.pages.group_menu', False))
    org_menu = toolkit.asbool(config.get('ckanext.pages.organization_menu', True))

    new_args = []
    for arg in args:
        if arg[0] == 'home.about' and not about_menu:
            continue
        if arg[0] == 'organizations_index' and not org_menu:
            continue
        if arg[0] == 'group_index' and not group_menu:
            continue
        new_args.append(arg)

    output = h.build_nav_main(*new_args)

    # add forum link
    forum_url = config.get('ckan.pages.forum.link', False)
    if forum_url:
        link = h.literal(u'<a href="{}" target="_blank">{}</a>'.format(forum_url, "Forum"))
        li = h.literal('<li>') + link + h.literal('</li>')
        output = output + li

    # do not display any private datasets in menu even for sysadmins
    pages_list = toolkit.get_action('ckanext_pages_list')(None, {'order': True, 'private': False})

    page_name = ''

    if (toolkit.c.action in ('pages_show', 'blog_show')
            and toolkit.c.controller == 'ckanext.pages.controller:PagesController'):
        page_name = toolkit.c.environ['routes.url'].current().split('/')[-1]

    for page in pages_list:
        type_ = 'blog' if page['page_type'] == 'blog' else 'pages'
        name = urllib.quote(page['name'].encode('utf-8')).decode('utf-8')
        title = cgi.escape(pages_page_title(h.lang(), page))
        if h.lang():
            link = h.literal(u'<a href="/{}/{}/{}">{}</a>'.format(h.lang(), type_, name, title))
        else:
            link = h.literal(u'<a href="/{}/{}">{}</a>'.format(type_, name, title))
        if page['name'] == page_name:
            li = h.literal('<li class="active">') + link + h.literal('</li>')
        else:
            li = h.literal('<li>') + link + h.literal('</li>')
        output = output + li

    return output


def render_content(content):
    allow_html = toolkit.asbool(config.get('ckanext.pages.allow_html', False))
    try:
        return h.render_markdown(content, allow_html=allow_html)
    except TypeError:
        # allow_html is only available in CKAN >= 2.3
        return h.render_markdown(content)


def get_wysiwyg_editor():
    return config.get('ckanext.pages.editor', '')


def get_recent_blog_posts(number=5, exclude=None):
    blog_list = toolkit.get_action('ckanext_pages_list')(
        None, {'order_publish_date': True, 'private': False,
               'page_type': 'blog'}
    )
    new_list = []
    for blog in blog_list:
        if exclude and blog['name'] == exclude:
            continue
        new_list.append(blog)
        if len(new_list) == number:
            break

    return new_list


def get_plus_icon():
    if toolkit.check_ckan_version(min_version='2.8'):
        return 'plus-square'
    return 'plus-sign-alt'


def pages_page_title(selected_lang, page_data):
    if selected_lang:
        if selected_lang == "nl" and page_data.get("title_nl", False):
            return page_data["title_nl"]
        elif selected_lang == "fr" and page_data.get("title_fr", False):
            return page_data["title_fr"]
        elif selected_lang == "de" and page_data.get("title_de", False):
            return page_data["title_de"]
    return page_data["title"]


class PagesPlugin(PagesPluginBase):
    p.implements(p.IConfigurer, inherit=True)
    p.implements(p.ITemplateHelpers, inherit=True)
    p.implements(p.IConfigurable, inherit=True)
    p.implements(p.IRoutes, inherit=True)
    p.implements(p.IActions, inherit=True)
    p.implements(p.IAuthFunctions, inherit=True)

    def update_config(self, config):
        self.organization_pages = toolkit.asbool(config.get('ckanext.pages.organization', False))
        self.group_pages = toolkit.asbool(config.get('ckanext.pages.group', False))

        toolkit.add_template_directory(config, 'theme/templates_main')
        if self.group_pages:
            toolkit.add_template_directory(config, 'theme/templates_group')
        if self.organization_pages:
            toolkit.add_template_directory(config, 'theme/templates_organization')

        toolkit.add_resource('fanstatic', 'pages')
        toolkit.add_public_directory(config, 'public')

        toolkit.add_resource('theme/public', 'ckanext-pages')
        toolkit.add_resource('theme/resources', 'pages-theme')
        toolkit.add_public_directory(config, 'theme/public')

    def configure(self, config):
        return

    def get_helpers(self):
        return {
            'build_nav_main': build_pages_nav_main,
            'render_content': render_content,
            'get_wysiwyg_editor': get_wysiwyg_editor,
            'get_recent_blog_posts': get_recent_blog_posts,
            'pages_get_plus_icon': get_plus_icon,
            'pages_page_title': pages_page_title
        }

    def after_map(self, map):
        controller = 'ckanext.pages.controller:PagesController'

        if self.organization_pages:
            map.connect('organization_pages_delete', '/organization/pages_delete/{id}{page:/.*|}',
                        action='org_delete', ckan_icon='delete', controller=controller)
            map.connect('organization_pages_edit', '/organization/pages_edit/{id}{page:/.*|}',
                        action='org_edit', ckan_icon='edit', controller=controller)
            map.connect('organization_pages_index', '/organization/pages/{id}',
                        action='org_show', ckan_icon='file', controller=controller,
                        highlight_actions='org_edit org_show', page='')
            map.connect('organization_pages', '/organization/pages/{id}{page:/.*|}',
                        action='org_show', ckan_icon='file', controller=controller,
                        highlight_actions='org_edit org_show')

        if self.group_pages:
            map.connect('group_pages_delete', '/group/pages_delete/{id}{page:/.*|}',
                        action='group_delete', ckan_icon='delete', controller=controller)
            map.connect('group_pages_edit', '/group/pages_edit/{id}{page:/.*|}',
                        action='group_edit', ckan_icon='edit', controller=controller)
            map.connect('group_pages_index', '/group/pages/{id}',
                        action='group_show', ckan_icon='file', controller=controller,
                        highlight_actions='group_edit group_show', page='')
            map.connect('group_pages', '/group/pages/{id}{page:/.*|}',
                        action='group_show', ckan_icon='file', controller=controller,
                        highlight_actions='group_edit group_show')

        map.connect('pages_delete', '/pages_delete{page:/.*|}',
                    action='pages_delete', ckan_icon='delete', controller=controller)
        map.connect('pages_edit', '/pages_edit{page:/.*|}',
                    action='pages_edit', ckan_icon='edit', controller=controller)
        map.connect('pages_index', '/pages',
                    action='pages_index', ckan_icon='file', controller=controller,
                    highlight_actions='pages_edit pages_index pages_show')
        map.connect('pages_show', '/pages{page:/.*|}',
                    action='pages_show', ckan_icon='file', controller=controller,
                    highlight_actions='pages_edit pages_index pages_show')
        map.connect('pages_upload', '/pages_upload',
                    action='pages_upload', controller=controller)

        map.connect('blog_delete', '/blog_delete{page:/.*|}',
                    action='blog_delete', ckan_icon='delete', controller=controller)
        map.connect('blog_edit', '/blog_edit{page:/.*|}',
                    action='blog_edit', ckan_icon='edit', controller=controller)
        map.connect('blog_index', '/blog',
                    action='blog_index', ckan_icon='file', controller=controller,
                    highlight_actions='blog_edit blog_index blog_show')
        map.connect('blog_show', '/blog{page:/.*|}',
                    action='blog_show', ckan_icon='file', controller=controller,
                    highlight_actions='blog_edit blog_index blog_show')
        return map

    def get_actions(self):
        actions_dict = {
            'ckanext_pages_show': actions.pages_show,
            'ckanext_pages_update': actions.pages_update,
            'ckanext_pages_delete': actions.pages_delete,
            'ckanext_pages_list': actions.pages_list,
            'ckanext_pages_upload': actions.pages_upload,
            'ckanext_menu_list': actions.menu_list,
        }
        if self.organization_pages:
            org_actions = {
                'ckanext_org_pages_show': actions.org_pages_show,
                'ckanext_org_pages_update': actions.org_pages_update,
                'ckanext_org_pages_delete': actions.org_pages_delete,
                'ckanext_org_pages_list': actions.org_pages_list,
            }
            actions_dict.update(org_actions)
        if self.group_pages:
            group_actions = {
                'ckanext_group_pages_show': actions.group_pages_show,
                'ckanext_group_pages_update': actions.group_pages_update,
                'ckanext_group_pages_delete': actions.group_pages_delete,
                'ckanext_group_pages_list': actions.group_pages_list,
            }
            actions_dict.update(group_actions)
        return actions_dict

    def get_auth_functions(self):
        return {
            'ckanext_pages_show': auth.pages_show,
            'ckanext_pages_update': auth.pages_update,
            'ckanext_pages_delete': auth.pages_delete,
            'ckanext_pages_list': auth.pages_list,
            'ckanext_pages_upload': auth.pages_upload,
            'ckanext_org_pages_show': auth.org_pages_show,
            'ckanext_org_pages_update': auth.org_pages_update,
            'ckanext_org_pages_delete': auth.org_pages_delete,
            'ckanext_org_pages_list': auth.org_pages_list,
            'ckanext_group_pages_show': auth.group_pages_show,
            'ckanext_group_pages_update': auth.group_pages_update,
            'ckanext_group_pages_delete': auth.group_pages_delete,
            'ckanext_group_pages_list': auth.group_pages_list,
        }


class TextBoxView(p.SingletonPlugin):
    p.implements(p.IConfigurer, inherit=True)
    p.implements(p.IResourceView, inherit=True)

    def update_config(self, config):
        toolkit.add_resource('textbox/theme', 'textbox')
        toolkit.add_template_directory(config, 'textbox/templates')

    def info(self):
        schema = {
            'content': [ignore_missing],
        }

        return {'name': 'wysiwyg',
                'title': 'Free Text',
                'icon': 'pencil',
                'iframed': False,
                'schema': schema,
                }

    def can_view(self, data_dict):
        return True

    def view_template(self, context, data_dict):
        return 'textbox_view.html'

    def form_template(self, context, data_dict):
        return 'textbox_form.html'

    def setup_template_variables(self, context, data_dict):
        return
