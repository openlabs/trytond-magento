# -*- coding: utf-8 -*-
"""
    test_party

    Tests party

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
import os
import sys
import unittest
DIR = os.path.abspath(os.path.normpath(
    os.path.join(
        __file__,
        '..', '..', '..', '..', '..', 'trytond'
    )
))
if os.path.isdir(DIR):
    sys.path.insert(0, os.path.dirname(DIR))

import trytond.tests.test_tryton
from trytond.tests.test_tryton import POOL, USER, DB_NAME, CONTEXT
from test_base import TestBase, load_json
from trytond.transaction import Transaction


class TestParty(TestBase):
    """
    Tests party
    """

    def test0010_create_party(self):
        """
        Tests if customers imported from magento is created as party
        in tryton
        """
        Party = POOL.get('party.party')
        MagentoParty = POOL.get('magento.website.party')

        with Transaction().start(DB_NAME, USER, CONTEXT):

            self.setup_defaults()

            Transaction().context.update({
                'magento_website': self.website1.id
            })
            magento_data = load_json('customers', '1')

            customer_name = u' '.join(
                [magento_data['firstname'], magento_data['lastname']]
            )

            self.assertFalse(
                Party.search([
                    ('name', '=', customer_name)
                ])
            )

            parties = MagentoParty.search([])
            self.assertEqual(len(parties), 0)

            # Create party
            party = Party.find_or_create_using_magento_data(magento_data)
            self.assert_(party)

            self.assertTrue(
                Party.search([
                    ('name', '=', customer_name)
                ])
            )
            self.assertTrue(len(party.contact_mechanisms), 1)
            self.assertTrue(party.contact_mechanisms[0].email)
            parties = MagentoParty.search([])

            self.assertEqual(len(parties), 1)

    def test0020_create_party_for_same_website(self):
        """
        Tests that party should be unique in a website
        """
        Party = POOL.get('party.party')
        MagentoParty = POOL.get('magento.website.party')

        with Transaction().start(DB_NAME, USER, CONTEXT):

            self.setup_defaults()

            Transaction().context.update({
                'magento_website': self.website1.id
            })

            magento_data = load_json('customers', '1')

            customer_name = u' '.join(
                [magento_data['firstname'], magento_data['lastname']]
            )

            parties = MagentoParty.search([])
            self.assertEqual(len(parties), 0)

            party = Party.find_or_create_using_magento_data(magento_data)
            self.assert_(party)

            self.assertTrue(
                Party.search([
                    ('name', '=', customer_name)
                ])
            )
            self.assertTrue(len(party.contact_mechanisms), 1)
            self.assertTrue(party.contact_mechanisms[0].email)

            parties = MagentoParty.search([])
            self.assertEqual(len(parties), 1)

            magento_data = load_json('customers', '1')

            # Create party with same magento_id and website_id it will not
            # create new one
            Party.find_or_create_using_magento_data(magento_data)
            parties = MagentoParty.search([])
            self.assertEqual(len(parties), 1)

            # Create party with different website
            Transaction().context.update({
                'magento_website': self.website2.id
            })
            magento_data = load_json('customers', '1')

            customer_name = u' '.join(
                [magento_data['firstname'], magento_data['lastname']]
            )

            party = Party.find_or_create_using_magento_data(magento_data)
            self.assert_(party)

            self.assertTrue(
                Party.search([
                    ('name', '=', customer_name)
                ], count=True),
                2
            )

            parties = MagentoParty.search([])
            self.assertEqual(len(parties), 2)

            # Create party with different magento_id
            Transaction().context.update({
                'magento_website': self.website1.id
            })

            magento_data = load_json('customers', '2')

            customer_name = u' '.join(
                [magento_data['firstname'], magento_data['lastname']]
            )

            self.assertFalse(
                Party.search([
                    ('name', '=', customer_name)
                ])
            )

            party = Party.find_or_create_using_magento_data(magento_data)
            self.assert_(party)

            self.assertTrue(
                Party.search([
                    ('name', '=', customer_name)
                ])
            )
            self.assertTrue(len(party.contact_mechanisms), 1)
            self.assertTrue(party.contact_mechanisms[0].email)

            parties = MagentoParty.search([])
            self.assertEqual(len(parties), 3)


def suite():
    """
    Test Suite
    """
    test_suite = trytond.tests.test_tryton.suite()
    test_suite.addTests(
        unittest.TestLoader().loadTestsFromTestCase(TestParty)
    )
    return test_suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
