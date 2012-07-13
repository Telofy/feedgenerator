#! /usr/bin/python
from setuptools import setup, find_packages

setup(
    name='feedgenerator',
    version='1.3.0',
    packages=find_packages('.'),
    extras_require={'test': ['requests']},

    author='Django Software Foundation',
    author_email='foundation@djangoproject.com',
    maintainer='Alexis Metaireau',
    maintainer_email='alexis@notmyidea.org',
    description='Standalone version of django.utils.feedgenerator',
    keywords=('feed', 'atom', 'rss'),
    url='https://github.com/ametaireau/feedgenerator',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules']
)
