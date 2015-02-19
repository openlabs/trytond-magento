# -*- coding: utf-8 -*-
"""
    tax.py

    :copyright: (c) 2015 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
from trytond.model import ModelView, ModelSQL, fields


class StoreViewTax(ModelSQL, ModelView):
    "Store View Tax"
    __name__ = "magento.store.store_view.tax"

    store_view = fields.Many2One(
        "magento.store.store_view", "Store View", required=True, select=True
    )
    tax_percent = fields.Numeric(
        "Tax Percent", digits=(16, 4), required=True, select=True
    )
    taxes = fields.Many2Many(
        "magento.store.store_view.tax_rel", "store_view_tax", "tax", "Taxes"
    )

    @classmethod
    def __setup__(cls):
        super(StoreViewTax, cls).__setup__()

        cls._error_messages.update({
            'unique_tax_percent_per_store_view':
            "Tax percent must be unique per store view"
        })
        cls._sql_constraints += [
            ('unique_tax_percent', 'UNIQUE(store_view, tax_percent)',
             'unique_tax_percent_per_store_view')
        ]


class StoreViewTaxRelation(ModelSQL):
    "Store View Tax Relation"
    __name__ = 'magento.store.store_view.tax_rel'

    store_view_tax = fields.Many2One(
        "magento.store.store_view.tax", 'Store View Tax', ondelete='CASCADE',
        select=True, required=True
    )
    tax = fields.Many2One(
        'account.tax', 'Tax', ondelete='RESTRICT',
        select=True, required=True
    )
