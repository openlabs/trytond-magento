#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    setup

    Setup

    :copyright: (c) 2013-2014 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
from setuptools import setup, Command
import re
import os
import ConfigParser
import unittest
import sys


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


class SQLiteTest(Command):
    """
    Run the tests on SQLite
    """
    description = "Run tests on SQLite"

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        if self.distribution.tests_require:
            self.distribution.fetch_build_eggs(self.distribution.tests_require)

        os.environ['TRYTOND_DATABASE_URI'] = 'sqlite://'
        os.environ['DB_NAME'] = ':memory:'

        from tests import suite
        test_result = unittest.TextTestRunner(verbosity=3).run(suite())

        if test_result.wasSuccessful():
            sys.exit(0)
        sys.exit(-1)

config = ConfigParser.ConfigParser()
config.readfp(open('tryton.cfg'))
info = dict(config.items('tryton'))
for key in ('depends', 'extras_depend', 'xml'):
    if key in info:
        info[key] = info[key].strip().splitlines()
major_version, minor_version, _ = info.get('version', '0.0.1').split('.', 2)
major_version = int(major_version)
minor_version = int(minor_version)
module_name = 'magento'

requires = [
    'magento',
]
for dep in info.get('depends', []):
    if not re.match(r'(ir|res|webdav)(\W|$)', dep):
        requires.append(
            'trytond_%s >= %s.%s, < %s.%s' % (
                dep, major_version, minor_version, major_version,
                minor_version + 1
            )
        )
requires.append(
    'trytond >= %s.%s, < %s.%s' % (
        major_version, minor_version, major_version, minor_version + 1
    )
)
test_requirements = [
    'mock',
]

setup(
    name='trytond_%s' % module_name,
    version=info.get('version', '0.0.1'),
    description='Tryton Magento Integration',
    author='Openlabs Technologies & Consulting (P) Limited',
    author_email='info@openlabs.co.in',
    url='https://github.com/openlabs/trytond-magento.git',
    package_dir={'trytond.modules.%s' % module_name: '.'},
    packages=[
        'trytond.modules.%s' % module_name,
        'trytond.modules.%s.tests' % module_name,
    ],
    package_data={
        'trytond.modules.%s' % module_name: info.get('xml', [])
            + ['tryton.cfg', 'view/*.xml']
            + info.get('translation', []),
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Plugins',
        'Framework :: Tryton',
        'Intended Audience :: Developers',
        'Intended Audience :: Financial and Insurance Industry',
        'Intended Audience :: Legal Industry',
        'Intended Audience :: Manufacturing',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Office/Business',
    ],
    license='BSD',
    tests_require=test_requirements,
    install_requires=requires,
    zip_safe=False,
    entry_points="""
    [trytond.modules]
    %s = trytond.modules.%s
    """ % (module_name, module_name),
    test_suite='tests',
    test_loader='trytond.test_loader:Loader',
    cmdclass={
        'test': SQLiteTest,
    },
)
