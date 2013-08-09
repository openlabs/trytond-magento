# -*- coding: utf-8 -*-
"""
    carrier

    Magento Carrier

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
from trytond.model import ModelView, ModelSQL, fields
from trytond.transaction import Transaction


__all__ = [
    'MagentoInstanceCarrier'
]


class MagentoInstanceCarrier(ModelSQL, ModelView):
    """
    Magento Instance carrier

    This model stores the carriers / shipping methods imported from magento
    each record here can be mapped to a carrier in tryton which will
    then be used for managing export of tracking info to magento.
    """
    __name__ = 'magento.instance.carrier'
    _rec_name = 'title'

    code = fields.Char("Code", readonly=True)
    carrier = fields.Many2One('carrier', 'Carrier')
    title = fields.Char('Title', readonly=True)
    instance = fields.Many2One(
        'magento.instance', 'Magento Instance', readonly=True
    )

    @classmethod
    def __setup__(cls):
        """
        Setup the class before adding to pool
        """
        super(MagentoInstanceCarrier, cls).__setup__()
        cls._sql_constraints += [
            (
                'code_instance_unique', 'unique(code, instance)',
                'Shipping methods must be unique in instance'
            )
        ]

    @classmethod
    def create_all_using_magento_data(cls, magento_data):
        """
        Creates record for list of carriers sent by magento.
        It creates a new carrier only if one with the same code does not
        exist for this instance.

        :param magento_data: List of Dictionary of carriers sent by magento
        :return: List of active records of carriers Created/Found
        """
        carriers = []
        for data in magento_data:
            carrier = cls.find_using_magento_data(data)
            if carrier:
                carriers.append(carrier)
            else:
                # Create carrier if not found
                carriers.append(cls.create_using_magento_data(data))
        return carriers

    @classmethod
    def create_using_magento_data(cls, carrier_data):
        """
         Create record for carrier data sent by magento

        :param carrier_data: Dictionary of carrier sent by magento
        :return: Active record of carrier created
        """
        carrier, = cls.create([{
            'code': carrier_data['code'],
            'title': carrier_data['label'],
            'instance': Transaction().context['magento_instance'],
        }])

        return carrier

    @classmethod
    def find_using_magento_data(cls, carrier_data):
        """
        Search for an existing carrier by matching code and instance.
        If found, return its active record else None

        :param carrier_data: Dictionary of carrier sent by magento
        :return: Active record of carrier found or None
        """
        try:
            carrier, = cls.search([
                ('code', '=', carrier_data['code']),
                ('instance', '=', Transaction().context['magento_instance']),
            ])
        except ValueError:
            return None
        else:
            return carrier
