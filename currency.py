# -*- coding: utf-8 -*-
"""
    currency

    Currency

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
from trytond.pool import PoolMeta


__all__ = ['Currency']
__metaclass__ = PoolMeta


class Currency:
    "Currency"
    __name__ = 'currency.currency'

    @classmethod
    def __setup__(cls):
        """
        Setup the class before adding to pool
        """
        super(Currency, cls).__setup__()
        cls._error_messages.update({
            'currency_not_found': 'Currency with code %s does not exist.',
        })

    @classmethod
    def search_using_magento_code(cls, currency_code):
        """
        Search for currency with given magento currency code.

        :param currency_code: currency code given by magento
        :return: Active record of currency if found else raises error
        """
        currencies = cls.search([('code', '=', currency_code)])

        if not currencies:
            return cls.raise_user_error('currency_not_found', (currency_code, ))

        return currencies[0]
