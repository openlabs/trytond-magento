# -*- coding: utf-8 -*-
"""
    test_sale

    Test Sale

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
import sys
import os
DIR = os.path.abspath(os.path.normpath(
    os.path.join(
        __file__,
        '..', '..', '..', '..', '..', 'trytond'
    )
))
if os.path.isdir(DIR):
    sys.path.insert(0, os.path.dirname(DIR))

import unittest
import trytond.tests.test_tryton
from trytond.transaction import Transaction
from trytond.tests.test_tryton import POOL, USER, DB_NAME, CONTEXT
from test_base import TestBase, load_json


class TestSale(TestBase):
    """
    Tests import of sale order
    """

    def test_0005_import_sale_order_states(self):
        """
        Test the import and creation of sale order states for an instance
        """
        MagentoOrderState = POOL.get('magento.order_state')

        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.setup_defaults()

            states_before_import = MagentoOrderState.search([])
            with Transaction().set_context({
                    'magento_instance': self.instance1.id}):
                states = MagentoOrderState.create_all_using_magento_data(
                    load_json('order-states', 'all')
                )
            states_after_import = MagentoOrderState.search([])

            self.assertTrue(states_after_import > states_before_import)

            for state in states:
                self.assertEqual(
                    state.instance.id, self.instance1.id
                )

    def test_0010_check_tryton_state(self):
        """
        Tests if correct tryton state is returned for each magento order state
        """
        MagentoOrderState = POOL.get('magento.order_state')

        self.assertEqual(
            MagentoOrderState.get_tryton_state('new'),
            {
                'tryton_state': 'sale.quotation',
                'invoice_method': 'order',
                'shipment_method': 'order'
            }
        )

        self.assertEqual(
            MagentoOrderState.get_tryton_state('holded'),
            {
                'tryton_state': 'sale.quotation',
                'invoice_method': 'order',
                'shipment_method': 'order'
            }
        )

        self.assertEqual(
            MagentoOrderState.get_tryton_state('pending_payment'),
            {
                'tryton_state': 'invoice.waiting',
                'invoice_method': 'order',
                'shipment_method': 'invoice'
            }
        )

        self.assertEqual(
            MagentoOrderState.get_tryton_state('payment_review'),
            {
                'tryton_state': 'invoice.waiting',
                'invoice_method': 'order',
                'shipment_method': 'invoice'
            }
        )

        self.assertEqual(
            MagentoOrderState.get_tryton_state('closed'),
            {
                'tryton_state': 'sale.done',
                'invoice_method': 'order',
                'shipment_method': 'order'
            }
        )

        self.assertEqual(
            MagentoOrderState.get_tryton_state('complete'),
            {
                'tryton_state': 'sale.done',
                'invoice_method': 'order',
                'shipment_method': 'order'
            }
        )

        self.assertEqual(
            MagentoOrderState.get_tryton_state('processing'),
            {
                'tryton_state': 'sale.processing',
                'invoice_method': 'order',
                'shipment_method': 'order'
            }
        )

        self.assertEqual(
            MagentoOrderState.get_tryton_state('cancelled'),
            {
                'tryton_state': 'sale.cancel',
                'invoice_method': 'manual',
                'shipment_method': 'manual'
            }
        )

    def test_0020_import_carriers(self):
        """
        Test If all carriers are being imported from magento
        """
        MagentoCarrier = POOL.get('magento.instance.carrier')

        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.setup_defaults()

            carriers_before_import = MagentoCarrier.search([])
            with Transaction().set_context({
                    'magento_instance': self.instance1.id
            }):
                carriers = MagentoCarrier.create_all_using_magento_data(
                    load_json('carriers', 'shipping_methods')
                )
                carriers_after_import = MagentoCarrier.search([])

                self.assertTrue(carriers_after_import > carriers_before_import)
                for carrier in carriers:
                    self.assertEqual(
                        carrier.instance.id,
                        Transaction().context['magento_instance']
                    )


def suite():
    """
    Test Suite
    """
    test_suite = trytond.tests.test_tryton.suite()
    test_suite.addTests(
        unittest.TestLoader().loadTestsFromTestCase(TestSale)
    )
    return test_suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
