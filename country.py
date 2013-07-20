# -*- coding: utf-8 -*-
"""
    country

    Country

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
from trytond.pool import PoolMeta


__all__ = ['Country']
__metaclass__ = PoolMeta


class Country:
    "Country"
    __name__ = 'country.country'

    @classmethod
    def __setup__(cls):
        """
        Setup the class before adding to pool
        """
        super(Country, cls).__setup__()
        cls._error_messages.update({
            'country_not_found': 'Country with ISO code %s does not exist.',
        })

    @classmethod
    def search_using_magento_code(cls, code):
        """
        Searches for country with given magento code.

        :param code: ISO code of country
        :return: Browse record of country if found else raises error
        """
        countries = cls.search([('code', '=', code)])

        if not countries:
            return cls.raise_user_error(
                "country_not_found", error_args=(code, )
            )

        return countries[0]
