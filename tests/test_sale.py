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

import magento
from mock import patch, MagicMock
import trytond.tests.test_tryton
from trytond.transaction import Transaction
from trytond.tests.test_tryton import POOL, USER, DB_NAME, CONTEXT
from test_base import TestBase, load_json


def mock_product_api(mock=None, data=None):
    if mock is None:
        mock = MagicMock(spec=magento.Product)

    handle = MagicMock(spec=magento.Product)
    handle.info.side_effect = lambda id: load_json('products', str(id))
    if data is None:
        handle.__enter__.return_value = handle
    else:
        handle.__enter__.return_value = data
    mock.return_value = handle
    return mock


def mock_order_api(mock=None, data=None):
    if mock is None:
        mock = MagicMock(spec=magento.Order)

    handle = MagicMock(spec=magento.Order)
    handle.info.side_effect = lambda id: load_json('orders', str(id))
    if data is None:
        handle.__enter__.return_value = handle
    else:
        handle.__enter__.return_value = data
    mock.return_value = handle
    return mock


def mock_customer_api(mock=None, data=None):
    if mock is None:
        mock = MagicMock(spec=magento.Customer)

    handle = MagicMock(spec=magento.Customer)
    handle.info.side_effect = lambda id: load_json('customers', str(id))
    if data is None:
        handle.__enter__.return_value = handle
    else:
        handle.__enter__.return_value = data
    mock.return_value = handle
    return mock


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

    def test_0030_import_sale_order_with_products_with_new(self):
        """
        Tests import of sale order using magento data with magento state as new
        """
        Sale = POOL.get('sale.sale')
        Party = POOL.get('party.party')
        Category = POOL.get('product.category')

        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.setup_defaults()

            with Transaction().set_context({
                'magento_instance': self.instance1.id,
                'magento_store_view': self.store_view,
                'magento_website': self.website1.id,
            }):

                category_tree = load_json('categories', 'category_tree')
                Category.create_tree_using_magento_data(category_tree)

                orders = Sale.search([])
                self.assertEqual(len(orders), 0)

                order_data = load_json('orders', '100000001')

                with patch(
                        'magento.Customer', mock_customer_api(), create=True):
                    Party.find_or_create_using_magento_id(
                        order_data['customer_id']
                    )

                with Transaction().set_context(company=self.company):
                # Create sale order using magento data
                    with patch(
                            'magento.Product', mock_product_api(), create=True):
                        order = Sale.find_or_create_using_magento_data(
                            order_data
                        )

                self.assertEqual(order.state, 'confirmed')

                orders = Sale.search([])
                self.assertEqual(len(orders), 1)

                # Item lines + shipping line should be equal to lines on tryton
                self.assertEqual(
                    len(order.lines), len(order_data['items']) + 1
                )

    def test_0035_import_sale_order_with_products_with_processing(self):
        """
        Tests import of sale order using magento data with magento state as
        processing
        """
        Sale = POOL.get('sale.sale')
        Party = POOL.get('party.party')
        Category = POOL.get('product.category')

        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.setup_defaults()

            with Transaction().set_context({
                'magento_instance': self.instance1.id,
                'magento_store_view': self.store_view,
                'magento_website': self.website1.id,
            }):

                category_tree = load_json('categories', 'category_tree')
                Category.create_tree_using_magento_data(category_tree)

                orders = Sale.search([])
                self.assertEqual(len(orders), 0)

                order_data = load_json('orders', '100000001-processing')

                with patch(
                        'magento.Customer', mock_customer_api(), create=True):
                    Party.find_or_create_using_magento_id(
                        order_data['customer_id']
                    )

                with Transaction().set_context(company=self.company):
                # Create sale order using magento data
                    with patch(
                            'magento.Product', mock_product_api(), create=True):
                        order = Sale.find_or_create_using_magento_data(
                            order_data
                        )

                self.assertEqual(order.state, 'processing')

                orders = Sale.search([])
                self.assertEqual(len(orders), 1)

                # Item lines + shipping line should be equal to lines on tryton
                self.assertEqual(
                    len(order.lines), len(order_data['items']) + 1
                )

    def test_0020_find_or_create_order_using_increment_id(self):
        """
        Tests finding and creating order using increment id
        """
        Sale = POOL.get('sale.sale')
        Party = POOL.get('party.party')
        Category = POOL.get('product.category')

        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.setup_defaults()
            with Transaction().set_context({
                'magento_instance': self.instance1.id,
                'magento_store_view': self.store_view.id,
                'magento_website': self.website1.id,
            }):

                category_tree = load_json('categories', 'category_tree')
                Category.create_tree_using_magento_data(category_tree)

                orders = Sale.search([])
                self.assertEqual(len(orders), 0)

                order_data = load_json('orders', '100000001')

                with patch(
                        'magento.Customer', mock_customer_api(), create=True):
                    Party.find_or_create_using_magento_id(
                        order_data['customer_id']
                    )

                with Transaction().set_context(company=self.company):
                    # Create sale order using magento increment_id
                    with patch('magento.Order', mock_order_api(), create=True):
                        with patch(
                            'magento.Product', mock_product_api(),
                            create=True
                        ):
                            order = \
                                Sale.find_or_create_using_magento_increment_id(
                                    order_data['increment_id']
                                )
                self.assertEqual(order.state, 'confirmed')

                orders = Sale.search([])

                self.assertEqual(len(orders), 1)

                # Item lines + shipping line should be equal to lines on tryton
                self.assertEqual(
                    len(order.lines), len(order_data['items']) + 1
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
