#! /usr/bin/python
from setuptools import setup, find_packages


NAME = 'feedgenerator'
PACKAGES = ['feedgenerator', 'feedgenerator.utils', 'feedgenerator.contrib',
        'feedgenerator.contrib.gis']
DESCRIPTION = 'Standalone version of django.utils.feedgenerator'

URL = "https://github.com/ametaireau/feedgenerator"

CLASSIFIERS = ['Development Status :: 5 - Production/Stable',
               'Environment :: Web Environment',
               'Intended Audience :: Developers',
               'License :: OSI Approved :: BSD License',
               'Operating System :: OS Independent',
               'Programming Language :: Python',
               'Topic :: Internet :: WWW/HTTP',
               'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
               'Topic :: Software Development :: Libraries :: Python Modules',
]

AUTHOR = 'Django Software Foundation'
AUTHOR_EMAIL = 'foundation@djangoproject.com'
MAINTAINER = 'Alexis Metaireau'
MAINTAINER_EMAIL= 'alexis@notmyidea.org'
KEYWORDS = "feed atom rss".split(' ')
VERSION = '1.3.0'

setup(
    name=NAME,
    version=VERSION,
    packages=PACKAGES,
    py_modules=MODULES,
    include_package_data = True,
    package_dir = {'': 'feedgenerator'},
    namespace_packages = ['feedgenerator'],
    install_requires=[
        'setuptools',
    ],

    # metadata for upload to PyPI
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    maintainer=MAINTAINER,
    maintainer_email=MAINTAINER_EMAIL,
    description=DESCRIPTION,
    keywords=KEYWORDS,
    url=URL,
    classifiers=CLASSIFIERS,
)
