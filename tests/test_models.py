# -*- coding: utf-8 -*-
"""
    test_models

    Tests Magento Instance, Website, Store and StoreView

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
import sys
import os
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


class TestModels(unittest.TestCase):
    '''
    Tests instance, website, store and store view
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

    def test0010create_instance(self):
        '''
        Tests if instance is created
        '''
        Instance = POOL.get('magento.instance')

        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            data = self.setup_defaults()

            with txn.set_context({'company': data['company']}):
                values = {
                    'name': 'Test Instance',
                    'url': 'some test url',
                    'api_user': 'admin',
                    'api_key': 'testkey',
                }

                instance, = Instance.create([values])

                self.assert_(instance)

    def test0020create_website(self):
        '''
        Tests if website is created under instance
        '''
        Instance = POOL.get('magento.instance')
        Website = POOL.get('magento.instance.website')

        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            data = self.setup_defaults()

            with txn.set_context({'company': data['company']}):
                values = {
                    'name': 'Test Instance',
                    'url': 'some test url',
                    'api_user': 'admin',
                    'api_key': 'testkey',
                }

                instance, = Instance.create([values])

                self.assert_(instance)

            values = {
                'name': 'A test website',
                'magento_id': 1,
                'code': 'test_code',
                'instance': instance.id,
            }

            website, = Website.create([values])
            self.assert_(website)

            self.assertEqual(website.company, instance.company)

    def test0030create_store(self):
        '''
        Tests if store is created under website
        '''
        Instance = POOL.get('magento.instance')
        Website = POOL.get('magento.instance.website')
        Store = POOL.get('magento.website.store')

        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            data = self.setup_defaults()

            with txn.set_context({'company': data['company']}):
                values = {
                    'name': 'Test Instance',
                    'url': 'some test url',
                    'api_user': 'admin',
                    'api_key': 'testkey',
                }

                instance, = Instance.create([values])

                self.assert_(instance)

            values = {
                'name': 'A test website',
                'magento_id': 1,
                'code': 'test_code',
                'instance': instance.id,
            }

            website, = Website.create([values])
            self.assert_(website)

            values = {
                'name': 'A test store',
                'magento_id': 1,
                'website': website.id,
            }

            store, = Store.create([values])
            self.assert_(store)

            self.assertEqual(store.company, website.company)
            self.assertEqual(store.instance, website.instance)

    def test0040create_store_view(self):
        '''
        Tests if store view is created for store
        '''
        Instance = POOL.get('magento.instance')
        Website = POOL.get('magento.instance.website')
        Store = POOL.get('magento.website.store')
        StoreView = POOL.get('magento.store.store_view')

        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            data = self.setup_defaults()

            with txn.set_context({'company': data['company']}):
                values = {
                    'name': 'Test Instance',
                    'url': 'some test url',
                    'api_user': 'admin',
                    'api_key': 'testkey',
                }

                instance, = Instance.create([values])

                self.assert_(instance)

            values = {
                'name': 'A test website',
                'magento_id': 1,
                'code': 'test_code',
                'instance': instance.id,
            }

            website, = Website.create([values])
            self.assert_(website)

            values = {
                'name': 'A test store',
                'magento_id': 1,
                'website': website.id,
            }

            store, = Store.create([values])
            self.assert_(store)

            values = {
                'name': 'A test store view',
                'code': 'test_code',
                'magento_id': 1,
                'store': store.id,
            }

            store_view, = StoreView.create([values])
            self.assert_(store_view)

            self.assertEqual(store_view.instance, store.instance)
            self.assertEqual(store_view.company, store.company)
            self.assertEqual(store_view.website, store.website)


def suite():
    """
    Test Suite
    """
    test_suite = trytond.tests.test_tryton.suite()
    test_suite.addTests(
        unittest.TestLoader().loadTestsFromTestCase(TestModels)
    )
    return test_suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
