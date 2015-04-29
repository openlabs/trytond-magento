# -*- coding: utf-8 -*-
"""
    tax.py

    :copyright: (c) 2015 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
from trytond.model import ModelView, ModelSQL, fields


class MagentoTax(ModelSQL, ModelView):
    "Magento Tax"
    __name__ = "sale.channel.magento.tax"

    # TODO: Add Domain
    channel = fields.Many2One(
        "sale.channel", "Channel", required=True, select=True
    )
    tax_percent = fields.Numeric(
        "Tax Percent", digits=(16, 4), required=True, select=True
    )
    taxes = fields.Many2Many(
        "sale.channel.magento.tax.tax_rel", "channel_tax", "tax", "Taxes"
    )

    @classmethod
    def __setup__(cls):
        super(MagentoTax, cls).__setup__()

        cls._error_messages.update({
            'unique_tax_percent_per_channel':
            "Tax percent must be unique per channel"
        })
        cls._sql_constraints += [
            ('unique_tax_percent', 'UNIQUE(channel, tax_percent)',
             'unique_tax_percent_per_channel')
        ]


class MagentoTaxRelation(ModelSQL):
    "Store View Tax Relation"
    __name__ = 'sale.channel.magento.tax.tax_rel'

    channel_tax = fields.Many2One(
        "sale.channel.magento.tax", 'Magento Channel Tax', ondelete='CASCADE',
        select=True, required=True
    )
    tax = fields.Many2One(
        'account.tax', 'Tax', ondelete='RESTRICT',
        select=True, required=True
    )
