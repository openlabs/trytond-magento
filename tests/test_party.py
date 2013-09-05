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
from trytond.exceptions import UserError


class TestParty(TestBase):
    """
    Tests party
    """

    def test0010_create_party(self):
        """
        Tests if customers imported from magento is created as party
        in tryton
        """
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
                self.Party.search([
                    ('name', '=', customer_name)
                ])
            )

            parties = MagentoParty.search([])
            self.assertEqual(len(parties), 0)

            # Create party
            party = self.Party.find_or_create_using_magento_data(magento_data)
            self.assert_(party)

            self.assertTrue(
                self.Party.search([
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

            party = self.Party.find_or_create_using_magento_data(magento_data)
            self.assert_(party)

            self.assertTrue(
                self.Party.search([
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
            self.Party.find_or_create_using_magento_data(magento_data)
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

            party = self.Party.find_or_create_using_magento_data(magento_data)
            self.assert_(party)

            self.assertTrue(
                self.Party.search([
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
                self.Party.search([
                    ('name', '=', customer_name)
                ])
            )

            party = self.Party.find_or_create_using_magento_data(magento_data)
            self.assert_(party)

            self.assertTrue(
                self.Party.search([
                    ('name', '=', customer_name)
                ])
            )
            self.assertTrue(len(party.contact_mechanisms), 1)
            self.assertTrue(party.contact_mechanisms[0].email)

            parties = MagentoParty.search([])
            self.assertEqual(len(parties), 3)

    def test0030_import_addresses_from_magento(self):
        """
        Test address import as party addresses and make sure no duplication
        is there.
        """
        Address = POOL.get('party.address')

        with Transaction().start(DB_NAME, USER, CONTEXT):

            self.setup_defaults()

            self.Subdivision.create([{
                'name': 'American Samoa',
                'code': 'US-AS',
                'type': 'state',
                'country': self.country1.id,
            }])

            # Load json of address data
            address_data = load_json('addresses', '1')

            # Check party address before import
            self.assertEqual(len(self.party.addresses), 1)

            # Check contact mechanism before import
            self.assertEqual(len(self.party.contact_mechanisms), 0)

            # Import address for party1 from magento
            address = Address.find_or_create_for_party_using_magento_data(
                self.party, address_data
            )

            # Check address after import
            self.assertEqual(len(self.party.addresses), 2)
            self.assertEqual(address.party, self.party)
            self.assertEqual(
                address.name, ' '.join([
                    address_data['firstname'], address_data['lastname']
                ])
            )
            self.assertEqual(address.street, address_data['street'])
            self.assertEqual(address.zip, address_data['postcode'])
            self.assertEqual(address.city, address_data['city'])
            self.assertEqual(address.country.code, address_data['country_id'])
            self.assertEqual(address.subdivision.name, address_data['region'])

            # Check contact mechnanism after import
            self.assertEqual(len(self.party.contact_mechanisms), 1)
            contact_mechanism, = self.party.contact_mechanisms
            self.assertEqual(contact_mechanism.type, 'phone')
            self.assertEqual(contact_mechanism.value, address_data['telephone'])

            # Try to import address data again.
            address = Address.find_or_create_for_party_using_magento_data(
                self.party, address_data
            )
            self.assertEqual(len(self.party.addresses), 2)
            self.assertEqual(len(self.party.contact_mechanisms), 1)

    def test0040_match_address(self):
        """
        Tests if address matching works as expected
        """
        Address = POOL.get('party.address')

        with Transaction().start(DB_NAME, USER, CONTEXT):

            self.setup_defaults()

            # Set magento website in context
            Transaction().context.update({
                'magento_website': self.website1.id
            })

            party_data = load_json('customers', '1')

            # Create party
            party = self.Party.find_or_create_using_magento_data(party_data)

            address_data = load_json('addresses', '1')

            address = Address.find_or_create_for_party_using_magento_data(
                party, address_data
            )

            # Same address imported again
            self.assertTrue(
                address.match_with_magento_data(load_json('addresses', '1'))
            )

            # Exactly similar address imported again
            self.assertTrue(
                address.match_with_magento_data(load_json('addresses', '1a'))
            )

            # Similar with different country. This will raise user error because
            # India doesn't have that state American Samoa.
            self.assertRaises(
                UserError, address.match_with_magento_data,
                load_json('addresses', '1b'),
            )

            # Similar with different state
            self.assertFalse(
                address.match_with_magento_data(load_json('addresses', '1c'))
            )

            # Similar with different street
            self.assertFalse(
                address.match_with_magento_data(load_json('addresses', '1e'))
            )


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
