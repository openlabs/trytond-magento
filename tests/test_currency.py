# -*- coding: utf-8 -*-
"""
    test_currency

    Tests Currency

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
import sys
import os
from decimal import Decimal
DIR = os.path.abspath(os.path.normpath(
    os.path.join(
        __file__, '..', '..', '..', '..', '..', 'trytond'
    )
))
if os.path.isdir(DIR):
    sys.path.insert(0, os.path.dirname(DIR))

import unittest

import trytond.tests.test_tryton
from trytond.tests.test_tryton import POOL, DB_NAME, USER, CONTEXT
from trytond.transaction import Transaction
from trytond.exceptions import UserError


class TestCurrency(unittest.TestCase):
    """
    Tests currency
    """

    def setUp(self):
        """
        Set up data used in the tests.
        this method is called before each test function execution.
        """
        trytond.tests.test_tryton.install_module('magento')

    def test_0010_get_currency_using_magento_code(self):
        """
        Tests if currency can be searched using magento code.
        """
        Currency = POOL.get('currency.currency')

        with Transaction().start(DB_NAME, USER, CONTEXT):

            # Create currencies
            currency1, currency2 = Currency.create([
                {
                    'name': 'US Dollar',
                    'code': 'USD',
                    'symbol': '$',
                    'rounding': Decimal('1'),
                }, {
                    'name': 'Indian Rupee',
                    'code': 'INR',
                    'symbol': 'Rs',
                    'rounding': Decimal('1'),
                }
            ])
            self.assert_(currency1)
            self.assert_(currency2)

            # Search currency with valid code
            self.assertEqual(
                Currency.search_using_magento_code('USD'), currency1
            )
            self.assertEqual(
                Currency.search_using_magento_code('INR'), currency2
            )

            # Try to search currency with invalid code
            self.assertRaises(
                UserError, Currency.search_using_magento_code, 'abc'
            )


def suite():
    """
    Test Suite
    """
    test_suite = trytond.tests.test_tryton.suite()
    test_suite.addTests(
        unittest.TestLoader().loadTestsFromTestCase(TestCurrency)
    )
    return test_suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
