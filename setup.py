# encoding: utf-8

from setuptools import setup, find_packages


setup(
    name='ckanext-pages',
    version='2.0.0',
    description='Basic CMS extension for CKAN (Belgian ITS fork)',
    long_description='',
    classifiers=[
        # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content :: Content Management System',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    keywords='CKAN CMS',
    author='David Raznick',
    author_email='david.raznick@gokfn.org',
    url='https://github.com/belgium-its-steering-committee/ckanext-pages',
    license='GNU Affero General Public License (AGPL) v3.0',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=['ckanext'],
    include_package_data=True,
    package_data={
            '': ['theme/*/*.html', 'theme/*/*/*.html', 'theme/*/*/*/*.html'],
    },
    zip_safe=False,
    install_requires=[
        'six', 'ckantoolkit'
    ],
    entry_points="""
        [ckan.plugins]
        pages=ckanext.pages.plugin:PagesPlugin
        textboxview=ckanext.pages.plugin:TextBoxView
        [babel.extractors]
        ckan = ckan.lib.extract:extract_ckan
        [paste.paster_command]
        pages = ckanext.pages.commands:PagesCommand
    """,
    message_extractors={
        'ckanext': [
            ('**.py', 'python', None),
            ('**.js', 'javascript', None),
            ('**/pages/theme/**.html', 'ckan', None),
        ],
    },
)
