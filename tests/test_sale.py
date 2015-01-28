# -*- coding: utf-8 -*-
"""
    test_sale

    Test Sale

    :copyright: (c) 2013-2014 by Openlabs Technologies & Consulting (P) Limited
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
from decimal import Decimal

import unittest
from datetime import datetime
from dateutil.relativedelta import relativedelta

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


def mock_shipment_api(mock=None, data=None):
    if mock is None:
        mock = MagicMock(spec=magento.Shipment)

    handle = MagicMock(spec=magento.Shipment)
    handle.create.side_effect = lambda *args, **kwargs: 'Shipment created'
    handle.addtrack.side_effect = lambda *args, **kwargs: True
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
                self.assertFalse(order.has_magento_exception)

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
                            'magento.Product', mock_product_api(), create=True
                    ):
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

    def test_0040_find_or_create_order_using_increment_id(self):
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

    def test_0050_export_order_status_to_magento(self):
        """
        Tests if order status is exported to magento
        """
        Sale = POOL.get('sale.sale')
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

                order_data = load_json('orders', '100000001-draft')

                with patch(
                        'magento.Customer', mock_customer_api(), create=True):
                    self.Party.find_or_create_using_magento_id(
                        order_data['customer_id']
                    )

                with Transaction().set_context(company=self.company):
                    # Create sale order using magento data
                    with patch(
                            'magento.Product', mock_product_api(), create=True):
                        order = Sale.find_or_create_using_magento_data(
                            order_data
                        )

                self.assertEqual(order.state, 'cancel')

                self.assertEqual(len(Sale.search([])), 1)

                with patch('magento.Order', mock_order_api(), create=True):
                    order_exported = \
                        self.store_view.export_order_status_for_store_view()

                    self.assertEqual(len(order_exported), 1)
                    self.assertEqual(order_exported[0], order)

    def test_0060_export_order_status_with_last_order_export_time_case1(self):
        """
        Tests that sale cannot be exported if last order export time is
        greater than sale's write date
        """
        Sale = POOL.get('sale.sale')
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

                order_data = load_json('orders', '100000001-draft')

                with patch(
                        'magento.Customer', mock_customer_api(), create=True):
                    self.Party.find_or_create_using_magento_id(
                        order_data['customer_id']
                    )

                with Transaction().set_context(company=self.company):
                    # Create sale order using magento data
                    with patch(
                            'magento.Product', mock_product_api(), create=True):
                        order = Sale.find_or_create_using_magento_data(
                            order_data
                        )

                self.assertEqual(order.state, 'cancel')
                self.assertEqual(len(Sale.search([])), 1)

                export_date = datetime.utcnow() + relativedelta(days=1)
                self.StoreView.write([self.store_view], {
                    'last_order_export_time': export_date
                })

                self.assertTrue(
                    self.store_view.last_order_export_time > order.write_date
                )

                with patch('magento.Order', mock_order_api(), create=True):
                    order_exported = \
                        self.store_view.export_order_status_for_store_view()

                    self.assertEqual(len(order_exported), 0)

    def test_0050_export_shipment(self):
        """
        Tests if shipments status is being exported for all the shipments
        related to store view
        """
        Sale = POOL.get('sale.sale')
        Party = POOL.get('party.party')
        Category = POOL.get('product.category')
        MagentoOrderState = POOL.get('magento.order_state')
        Carrier = POOL.get('carrier')
        ProductTemplate = POOL.get('product.template')
        MagentoCarrier = POOL.get('magento.instance.carrier')
        Shipment = POOL.get('stock.shipment.out')
        Uom = POOL.get('product.uom')

        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.setup_defaults()
            with Transaction().set_context({
                'magento_instance': self.instance1.id,
                'magento_store_view': self.store_view,
                'magento_website': self.website1.id,
            }):

                MagentoOrderState.create_all_using_magento_data(
                    load_json('order-states', 'all'),
                )

                category_tree = load_json('categories', 'category_tree')
                Category.create_tree_using_magento_data(category_tree)

                orders = Sale.search([])
                self.assertEqual(len(orders), 0)

                order_data = load_json('orders', '100000001')

                with patch(
                        'magento.Customer', mock_customer_api(), create=True):
                    party = Party.find_or_create_using_magento_id(
                        order_data['customer_id']
                    )

                with Transaction().set_context(company=self.company):
                    # Create sale order using magento data
                    with patch(
                            'magento.Product', mock_product_api(), create=True
                    ):
                        order = Sale.find_or_create_using_magento_data(
                            order_data
                        )

                mag_carriers = MagentoCarrier.create_all_using_magento_data(
                    load_json('carriers', 'shipping_methods')
                )

                uom, = Uom.search([('name', '=', 'Unit')], limit=1)
                product, = ProductTemplate.create([
                    {
                        'name': 'Shipping product',
                        'list_price': Decimal('100'),
                        'cost_price': Decimal('1'),
                        'type': 'service',
                        'account_expense': self.get_account_by_kind('expense'),
                        'account_revenue': self.get_account_by_kind('revenue'),
                        'default_uom': uom.id,
                        'sale_uom': uom.id,
                        'products': [('create', [{
                            'code': 'code',
                            'description': 'This is a product description',
                        }])]
                    }]
                )

                # Create carrier
                carrier, = Carrier.create([{
                    'party': party.id,
                    'carrier_product': product.products[0].id,
                }])
                MagentoCarrier.write([mag_carriers[0]], {
                    'carrier': carrier.id,
                })

                Sale.write([order], {'invoice_method': 'manual'})
                order = Sale(order.id)
                Sale.confirm([order])
                with Transaction().set_user(0, set_context=True):
                    Sale.process([order])
                shipment, = Shipment.search([])

                Shipment.write([shipment], {
                    'carrier': carrier.id,
                    'tracking_number': '1234567890',
                })
                Shipment.assign([shipment])
                Shipment.pack([shipment])
                Shipment.done([shipment])

                shipment = Shipment(shipment.id)

                self.assertFalse(shipment.magento_increment_id)

                with patch(
                    'magento.Shipment', mock_shipment_api(), create=True
                ):

                    self.store_view.export_shipment_status_to_magento()

                    shipment = Shipment(shipment.id)
                    self.assertTrue(shipment.magento_increment_id)

                    # Export Tracking info
                    self.assertEqual(
                        shipment.export_tracking_info_to_magento(),
                        True
                    )

    def test_0070_export_order_status_with_last_order_export_time_case2(self):
        """
        Tests that sale can be exported if last order export time is
        smaller than sale's write date
        """
        Sale = POOL.get('sale.sale')
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

                order_data = load_json('orders', '100000001-draft')

                with patch(
                        'magento.Customer', mock_customer_api(), create=True):
                    self.Party.find_or_create_using_magento_id(
                        order_data['customer_id']
                    )

                with Transaction().set_context(company=self.company):
                    # Create sale order using magento data
                    with patch(
                            'magento.Product', mock_product_api(), create=True):
                        order = Sale.find_or_create_using_magento_data(
                            order_data
                        )

                self.assertEqual(order.state, 'cancel')
                self.assertEqual(len(Sale.search([])), 1)

                export_date = datetime.utcnow() - relativedelta(days=1)
                self.StoreView.write([self.store_view], {
                    'last_order_export_time': export_date
                })

                self.assertTrue(
                    self.store_view.last_order_export_time < order.write_date
                )

                with patch('magento.Order', mock_order_api(), create=True):
                    order_exported = \
                        self.store_view.export_order_status_for_store_view()

                    self.assertEqual(len(order_exported), 1)
                    self.assertEqual(order_exported[0], order)

    def test_0080_import_sale_order_with_bundle_product(self):
        """
        Tests import of sale order with bundle product using magento data
        """
        Sale = POOL.get('sale.sale')
        ProductTemplate = POOL.get('product.template')
        Category = POOL.get('product.category')
        MagentoOrderState = POOL.get('magento.order_state')

        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.setup_defaults()

            with Transaction().set_context({
                'magento_instance': self.instance1.id,
                'magento_store_view': self.store_view.id,
                'magento_website': self.website1.id,
            }):

                MagentoOrderState.create_all_using_magento_data(
                    load_json('order-states', 'all'),
                )

                category_tree = load_json('categories', 'category_tree')
                Category.create_tree_using_magento_data(category_tree)

                orders = Sale.search([])
                self.assertEqual(len(orders), 0)

                order_data = load_json('orders', '300000001')

                with patch(
                        'magento.Customer', mock_customer_api(), create=True):
                    self.Party.find_or_create_using_magento_id(
                        order_data['customer_id']
                    )

                with Transaction().set_context(company=self.company):
                    # Create sale order using magento data
                    with patch(
                        'magento.Product', mock_product_api(), create=True
                    ):
                        order = Sale.find_or_create_using_magento_data(
                            order_data
                        )

                self.assertEqual(order.state, 'confirmed')

                orders = Sale.search([])
                self.assertEqual(len(orders), 1)

                # Item lines + shipping line should be equal to lines on tryton
                self.assertEqual(len(order.lines), 2)

                self.assertEqual(
                    order.total_amount, Decimal(order_data['base_grand_total'])
                )

                # There should be a BoM for the bundle product
                product_template = \
                    ProductTemplate.find_or_create_using_magento_id(158)
                product = product_template.products[0]
                self.assertEqual(len(product.boms), 1)
                self.assertEqual(
                    len(product.boms[0].bom.inputs), 2
                )

    def test_0090_import_sale_order_with_bundle_product_check_duplicate(self):
        """
        Tests import of sale order with bundle product using magento data
        This tests that the duplication of BoMs doesnot happen
        """
        Sale = POOL.get('sale.sale')
        ProductTemplate = POOL.get('product.template')
        Category = POOL.get('product.category')
        MagentoOrderState = POOL.get('magento.order_state')

        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.setup_defaults()
            with Transaction().set_context({
                'magento_instance': self.instance1.id,
                'magento_store_view': self.store_view.id,
                'magento_website': self.website1.id,
            }):

                MagentoOrderState.create_all_using_magento_data(
                    load_json('order-states', 'all'),
                )

                category_tree = load_json('categories', 'category_tree')
                Category.create_tree_using_magento_data(category_tree)

                order_data = load_json('orders', '300000001')

                with patch(
                        'magento.Customer', mock_customer_api(), create=True):
                    self.Party.find_or_create_using_magento_id(
                        order_data['customer_id']
                    )

                with Transaction().set_context({'company': self.company.id}):
                    # Create sale order using magento data
                    with patch(
                        'magento.Product', mock_product_api(), create=True
                    ):
                        Sale.find_or_create_using_magento_data(order_data)

                # There should be a BoM for the bundle product
                product_template = \
                    ProductTemplate.find_or_create_using_magento_id(158)
                product = product_template.products[0]
                self.assertTrue(len(product.boms), 1)
                self.assertTrue(len(product.boms[0].bom.inputs), 2)

                order_data = load_json('orders', '300000001-a')

                # Create sale order using magento data
                with patch('magento.Product', mock_product_api(), create=True):
                    Sale.find_or_create_using_magento_data(order_data)

                # There should be a BoM for the bundle product
                product_template = \
                    ProductTemplate.find_or_create_using_magento_id(
                        158
                    )
                self.assertEqual(len(product.boms), 1)
                self.assertEqual(len(product.boms[0].bom.inputs), 2)

    def test_0100_import_sale_with_bundle_plus_child_separate(self):
        """
        Tests import of sale order with bundle product using magento data
        One of the children of the bundle is bought separately too
        Make sure that the lines are created correctly
        """
        Sale = POOL.get('sale.sale')
        Category = POOL.get('product.category')
        MagentoOrderState = POOL.get('magento.order_state')

        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.setup_defaults()
            with Transaction().set_context({
                'magento_instance': self.instance1.id,
                'magento_store_view': self.store_view.id,
                'magento_website': self.website1.id,
            }):

                MagentoOrderState.create_all_using_magento_data(
                    load_json('order-states', 'all'),
                )

                category_tree = load_json('categories', 'category_tree')
                Category.create_tree_using_magento_data(category_tree)

                order_data = load_json('orders', '100000004')

                with patch(
                        'magento.Customer', mock_customer_api(), create=True):
                    self.Party.find_or_create_using_magento_id(
                        order_data['customer_id']
                    )

                with Transaction().set_context({'company': self.company.id}):
                    # Create sale order using magento data
                    with patch(
                        'magento.Product', mock_product_api(), create=True
                    ):
                        order = Sale.find_or_create_using_magento_data(
                            order_data
                        )

                self.assertEqual(
                    order.total_amount, Decimal(order_data['base_grand_total'])
                )

                # Item lines + shipping line should be equal to lines on tryton
                self.assertEqual(len(order.lines), 3)


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
