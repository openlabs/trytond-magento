# -*- coding: utf-8 -*-
"""
    test_country

    Tests country

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
import sys
import os
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


class TestCountry(unittest.TestCase):
    """
    Tests country
    """

    def setUp(self):
        """
        Set up data used in the tests.
        this method is called before each test function execution.
        """
        trytond.tests.test_tryton.install_module('magento')

    def test_0010_search_country_with_valid_code(self):
        """
        Tests if country can be searched using magento code
        """
        Country = POOL.get('country.country')

        with Transaction().start(DB_NAME, USER, CONTEXT):

            country = Country.create([{
                'name': 'United States',
                'code': 'US',
            }])
            self.assert_(country)

            code = 'US'

            country, = Country.search([('code', '=', code)])

            self.assertEqual(
                Country.search_using_magento_code(code),
                country
            )

    def test_0020_search_country_with_invalid_code(self):
        """
        Tests if error is raised for searching country with invalid code
        """
        Country = POOL.get('country.country')

        with Transaction().start(DB_NAME, USER, CONTEXT):

            code = 'abc'

            self.assertFalse(Country.search([('code', '=', code)]))

            self.assertRaises(
                UserError,
                Country.search_using_magento_code, code
            )

    def test_0030_search_state_with_valid_region(self):
        """
        Tests if state can be searched using magento region
        """
        Country = POOL.get('country.country')
        Subdivision = POOL.get('country.subdivision')

        with Transaction().start(DB_NAME, USER, CONTEXT):

            country, = Country.create([{
                'name': 'United States',
                'code': 'US',
            }])
            self.assert_(country)
            subdivision, = Subdivision.create([{
                'name': 'Florida',
                'code': 'US-FL',
                'country': country.id,
                'type': 'state',
            }])

            region = 'Florida'

            self.assertEqual(
                Subdivision.search_using_magento_region(region, country),
                subdivision
            )

    def test_0040_search_state_with_invalid_region(self):
        """
        Tests if error is raised for searching state with invalid region
        """
        Country = POOL.get('country.country')
        Subdivision = POOL.get('country.subdivision')

        with Transaction().start(DB_NAME, USER, CONTEXT):

            country, = Country.create([{
                'name': 'United States',
                'code': 'US',
            }])
            self.assert_(country)

            region = 'abc'

            self.assertFalse(
                Subdivision.search([
                    ('name', 'ilike', region),
                    ('country', '=', country.id)
                ])
            )

            self.assertRaises(
                UserError,
                Subdivision.search_using_magento_region, region, country
            )


def suite():
    """
    Test Suite
    """
    test_suite = trytond.tests.test_tryton.suite()
    test_suite.addTests(
        unittest.TestLoader().loadTestsFromTestCase(TestCountry)
    )
    return test_suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
