# -*- coding: utf-8 -*-
"""
    test_website_import

    Tests import of Magento Websites, Stores and StoreViews

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
import sys
import os
import json
DIR = os.path.abspath(os.path.normpath(
    os.path.join(
        __file__,
        '..', '..', '..', '..', '..', 'trytond'
    )
))
if os.path.isdir(DIR):
    sys.path.insert(0, os.path.dirname(DIR))

import unittest
import trytond.tests.test_tryton
from trytond.transaction import Transaction
from trytond.tests.test_tryton import POOL, USER, DB_NAME, CONTEXT


ROOT_JSON_FOLDER = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'json'
)


def load_json(resource, filename):
    """Reads the json file from the filesystem and returns the json loaded as
    python objects

    On filesystem, the files are kept in this format:
        json----
              |
            resource----
                       |
                       filename

    :param resource: The prestashop resource for which the file has to be
                     fetched. It is same as the folder name in which the files
                     are kept.
    :param filename: The name of the file to be fethced without `.json`
                     extension.
    :returns: Loaded json from the contents of the file read.
    """
    file_path = os.path.join(
        ROOT_JSON_FOLDER, resource, str(filename)
    ) + '.json'

    return json.loads(open(file_path).read())


class TestWebsiteImport(unittest.TestCase):
    '''
    Tests import of Magento Websites, Stores and StoreViews
    '''

    def setUp(self):
        """
        Set up data used in the tests.
        this method is called before each test function execution.
        """
        trytond.tests.test_tryton.install_module('magento')

    def setup_defaults(self):
        """
        Create setup defaults
        """
        Currency = POOL.get('currency.currency')
        Company = POOL.get('company.company')
        Party = POOL.get('party.party')

        party, = Party.create([{
            'name': 'ABC',
        }])
        usd, = Currency.create([{
            'name': 'US Dollar',
            'code': 'USD',
            'symbol': '$',
        }])
        company, = Company.create([{
            'party': party.id,
            'currency': usd.id,
        }])

        return {
            'company': company
        }

    def test_0010_import_websites(self):
        """Test the import of websites
        """
        Instance = POOL.get('magento.instance')
        Website = POOL.get('magento.instance.website')

        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            data = self.setup_defaults()
            with txn.set_context({'company': data['company']}):
                instance, = Instance.create([{
                    'name': 'Test Instance',
                    'url': 'some test url',
                    'api_user': 'admin',
                    'api_key': 'testkey',
                }])
                websites_before_import = Website.search([])
                Website.find_or_create(instance, load_json('core', 'website'))
                websites_after_import = Website.search([])

                self.assertTrue(
                    websites_after_import > websites_before_import
                )

    def test_0020_import_stores(self):
        """Test the import of stores
        """
        Instance = POOL.get('magento.instance')
        Website = POOL.get('magento.instance.website')
        Store = POOL.get('magento.website.store')

        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            data = self.setup_defaults()
            with txn.set_context({'company': data['company']}):
                instance, = Instance.create([{
                    'name': 'Test Instance',
                    'url': 'some test url',
                    'api_user': 'admin',
                    'api_key': 'testkey',
                }])
                website = Website.find_or_create(
                    instance, load_json('core', 'website')
                )

                stores_before_import = Store.search([])
                Store.find_or_create(website, load_json('core', 'store'))
                stores_after_import = Store.search([])

                self.assertTrue(
                    stores_after_import > stores_before_import
                )

    def test_0030_import_stores(self):
        """Test the import of stores
        """
        Instance = POOL.get('magento.instance')
        Website = POOL.get('magento.instance.website')
        Store = POOL.get('magento.website.store')
        StoreView = POOL.get('magento.store.store_view')

        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            data = self.setup_defaults()
            with txn.set_context({'company': data['company']}):
                instance, = Instance.create([{
                    'name': 'Test Instance',
                    'url': 'some test url',
                    'api_user': 'admin',
                    'api_key': 'testkey',
                }])
                website = Website.find_or_create(
                    instance, load_json('core', 'website')
                )
                store = Store.find_or_create(
                    website, load_json('core', 'store')
                )

                store_views_before_import = StoreView.search([])
                StoreView.find_or_create(store, load_json(
                    'core', 'store_view')
                )
                store_views_after_import = StoreView.search([])

                self.assertTrue(
                    store_views_after_import > store_views_before_import
                )


def suite():
    """
    Test Suite
    """
    test_suite = trytond.tests.test_tryton.suite()
    test_suite.addTests(
        unittest.TestLoader().loadTestsFromTestCase(TestWebsiteImport)
    )
    return test_suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
