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
from trytond.tests.test_tryton import USER, DB_NAME, CONTEXT
from tests.test_base import TestBase


class TestModels(TestBase):
    '''
    Tests instance, website, store and store view
    '''

    def test0010create_instance(self):
        '''
        Tests if instance is created
        '''
        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            self.setup_defaults()

            with txn.set_context({'company': self.company.id}):
                values = {
                    'name': 'Test Instance',
                    'url': 'some test url',
                    'api_user': 'admin',
                    'api_key': 'testkey',
                    'default_account_expense':
                        self.get_account_by_kind('expense'),
                    'default_account_revenue':
                        self.get_account_by_kind('revenue'),
                }

                instance, = self.Instance.create([values])

                self.assert_(instance)

    def test0020create_website(self):
        '''
        Tests if website is created under instance
        '''
        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.setup_defaults()

            values = {
                'name': 'A test website',
                'magento_id': 3,
                'code': 'test_code',
                'instance': self.instance1.id,
            }

            website, = self.Website.create([values])
            self.assert_(website)

            self.assertEqual(website.company, self.instance1.company)

    def test0030create_store(self):
        '''
        Tests if store is created under website
        '''
        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.setup_defaults()

            values = {
                'name': 'A test store',
                'magento_id': 2,
                'website': self.website1.id,
            }

            store, = self.Store.create([values])
            self.assert_(store)

            self.assertEqual(store.company, self.website1.company)
            self.assertEqual(store.instance, self.website1.instance)

    def test0040create_store_view(self):
        '''
        Tests if store view is created for store
        '''
        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.setup_defaults()

            values = {
                'name': 'A test store view',
                'code': 'test_code',
                'magento_id': 2,
                'store': self.store.id,
            }

            store_view, = self.StoreView.create([values])
            self.assert_(store_view)

            self.assertEqual(store_view.instance, self.store.instance)
            self.assertEqual(store_view.company, self.store.company)
            self.assertEqual(store_view.website, self.store.website)


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
