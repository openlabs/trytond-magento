# -*- coding: utf-8 -*-
"""
    party

    Party

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
from trytond.model import ModelSQL, ModelView, fields
from trytond.pool import PoolMeta, Pool
from trytond.transaction import Transaction


__all__ = ['Party', 'MagentoWebsiteParty', 'Address']
__metaclass__ = PoolMeta


class Party:
    "Party"
    __name__ = 'party.party'

    magento_ids = fields.One2Many(
        "magento.website.party", "party", "Magento IDs", readonly=True
    )

    @classmethod
    def __setup__(cls):
        """
        Setup the class before adding to pool
        """
        super(Party, cls).__setup__()
        cls._error_messages.update({
            'website_not_found': 'Website does not exist in context'
        })

    @classmethod
    def find_or_create_using_magento_data(cls, magento_data):
        """
        Looks for the customer whose magento_data is sent by magento against
        the magento_website in context.
        If a record exists for this, return that else create a new one and
        return

        :param magento_data: Dictionary of values for customer sent by magento
        :return: Active record of record created/found
        """
        if not Transaction().context['magento_website']:
            return cls.raise_user_error('website_not_found')

        party = cls.find_using_magento_data(magento_data)

        if not party:
            party = cls.create_using_magento_data(magento_data)

        return party

    @classmethod
    def create_using_magento_data(cls, magento_data):
        """
        Creates record of customer values sent by magento

        :param magento_data: Dictionary of values for customer sent by magento
        :return: Active record of record created
        """
        party, = cls.create([{
            'name': u' '.join(
                [magento_data['firstname'], magento_data['lastname']]
            ),
            'magento_ids': [
                ('create', [{
                    'magento_id': magento_data['customer_id'],
                    'website': Transaction().context['magento_website'],
                }])
            ],
            'contact_mechanisms': [
                ('create', [{
                    'email': magento_data['email']
                }])
            ]
        }])

        return party

    @classmethod
    def find_using_magento_data(cls, magento_data):
        """
        Looks for the customer whose magento_data is sent by magento against
        the magento_website_id in context.
        If record exists returns that else None

        :param magento_data: Dictionary of values for customer sent by magento
        :return: Active record of record found or None
        """
        MagentoParty = Pool().get('magento.website.party')

        parties = MagentoParty.search([
            ('magento_id', '=', magento_data['customer_id']),
            ('website', '=', Transaction().context['magento_website'])
        ])
        return parties and parties[0] or None


class MagentoWebsiteParty(ModelSQL, ModelView):
    "Magento Website Party"
    __name__ = 'magento.website.party'

    magento_id = fields.Integer('Magento ID', readonly=True)
    website = fields.Many2One(
        'magento.instance.website', 'Website', required=True, readonly=True
    )
    party = fields.Many2One(
        'party.party', 'Party', required=True, readonly=True
    )

    @classmethod
    def __setup__(cls):
        """
        Setup the class before adding to pool
        """
        super(MagentoWebsiteParty, cls).__setup__()
        cls._sql_constraints += [
            (
                'magento_id_website_unique', 'UNIQUE(magento_id, website)',
                'A party must be unique in a website'
            )
        ]


class Address:
    "Address"
    __name__ = 'party.address'

    def match_with_magento_data(self, address_data):
        """
        Match the current address with the address_record.
        Match all the fields of the address, i.e., streets, city, subdivision
        and country. For any deviation in any field, returns False.

        :param address_data: Dictionary of address data from magento
        :return: True if address matches else False
        """
        Country = Pool().get('country.country')
        Subdivision = Pool().get('country.subdivision')

        # Check if the name matches
        if self.name != ' '.join(
            [address_data['firstname'], address_data['lastname']]
        ):
            return False

        # Find country and subdivision based on magento data
        country = None
        subdivision = None
        if address_data['country_id']:
            country = Country.search_using_magento_code(
                address_data['country_id']
            )
            if address_data['region']:
                subdivision = Subdivision.search_using_magento_region(
                    address_data['region'], country
                )

        if not all([
            self.street == (address_data['street'] or None),
            self.zip == (address_data['postcode'] or None),
            self.city == (address_data['city'] or None),
            self.country == country,
            self.subdivision == subdivision,
        ]):
            return False

        return True

    @classmethod
    def find_or_create_for_party_using_magento_data(cls, party, address_data):
        """
        Look for the address in tryton corresponding to the address_record.
        If found, return the same else create a new one and return that.

        :param party: Party active record
        :param address_data: Dictionary of address data from magento
        :return: Active record of address created/found
        """
        for address in party.addresses:
            if address.match_with_magento_data(address_data):
                break

        else:
            address = cls.create_for_party_using_magento_data(
                party, address_data
            )

        return address

    @classmethod
    def create_for_party_using_magento_data(cls, party, address_data):
        """
        Create address from the address record given and link it to the
        party.

        :param party: Party active record
        :param address_data: Dictionary of address data from magento
        :return: Active record of created address
        """
        Country = Pool().get('country.country')
        Subdivision = Pool().get('country.subdivision')
        ContactMechanism = Pool().get('party.contact_mechanism')

        country = None
        subdivision = None
        if address_data['country_id']:
            country = Country.search_using_magento_code(
                address_data['country_id']
            )
            if address_data['region']:
                subdivision = Subdivision.search_using_magento_region(
                    address_data['region'], country
                )

        address, = cls.create([{
            'party': party.id,
            'name': ' '.join([
                address_data['firstname'], address_data['lastname']
            ]),
            'street': address_data['street'],
            'zip': address_data['postcode'],
            'city': address_data['city'],
            'country': country.id,
            'subdivision': subdivision.id,
        }])

        # Create phone as contact mechanism
        if not ContactMechanism.search([
            ('party', '=', party.id),
            ('type', 'in', ['phone', 'mobile']),
            ('value', '=', address_data['telephone']),
        ]):
            ContactMechanism.create([{
                'party': party.id,
                'type': 'phone',
                'value': address_data['telephone'],
            }])

        return address
