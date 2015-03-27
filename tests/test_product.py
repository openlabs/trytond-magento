# -*- coding: utf-8 -*-
"""
    test_product

    :copyright: (c) 2013-2014 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
import sys
import os
from decimal import Decimal

import unittest
import magento
from mock import patch, MagicMock

import trytond.tests.test_tryton
from trytond.tests.test_tryton import POOL, USER, DB_NAME, CONTEXT
from test_base import TestBase, load_json
from trytond.transaction import Transaction

DIR = os.path.abspath(os.path.normpath(
    os.path.join(
        __file__,
        '..', '..', '..', '..', '..', 'trytond'
    )
))
if os.path.isdir(DIR):
    sys.path.insert(0, os.path.dirname(DIR))


def mock_inventory_api(mock=None, data=None):
    if mock is None:
        mock = MagicMock(spec=magento.Inventory)

    handle = MagicMock(spec=magento.Inventory)
    handle.update.side_effect = lambda id, data: True
    if data is None:
        handle.__enter__.return_value = handle
    else:
        handle.__enter__.return_value = data
    mock.return_value = handle
    return mock


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


class TestProduct(TestBase):
    '''
    Tests the methods of product
    '''

    def test_0010_import_product_categories(self):
        """
        Test the import of product category using magento data
        """
        Category = POOL.get('product.category')
        MagentoCategory = POOL.get('magento.instance.product_category')

        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            self.setup_defaults()
            categories_before_import = Category.search([], count=True)

            category_tree = load_json('categories', 'category_tree')
            with txn.set_context({'current_channel': self.channel1.id}):
                Category.create_tree_using_magento_data(category_tree)

                categories_after_import = Category.search([], count=True)

                self.assertTrue(
                    categories_before_import < categories_after_import
                )
                # Look for Root Category
                root_categories = Category.search([
                    ('parent', '=', None)
                ])

                self.assertEqual(len(root_categories[0].magento_ids), 1)

                root_category = root_categories[0]

                self.assertEqual(root_category.magento_ids[0].magento_id, 1)

                self.assertEqual(len(root_category.childs), 1)
                self.assertEqual(len(root_category.childs[0].childs), 4)

                self.assertTrue(
                    MagentoCategory.search([
                        ('channel', '=', self.channel1)
                    ], count=True) > 0
                )
                self.assertTrue(
                    MagentoCategory.search([
                        ('channel', '=', self.channel2)
                    ], count=True) == 0
                )

    def test_0020_import_simple_product(self):
        """
        Test the import of simple product using Magento Data
        """
        Category = POOL.get('product.category')
        Product = POOL.get('product.product')
        ProductSaleChannelListing = POOL.get('product.product.channel_listing')

        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            self.setup_defaults()

            category_data = load_json('categories', '8')

            with txn.set_context({
                'current_channel': self.channel1.id,
                'company': self.company.id,
            }):
                Category.create_using_magento_data(category_data)

                products_before_import = Product.search([], count=True)

                product_data = load_json('products', '17')
                product = Product.find_or_create_using_magento_data(
                    product_data
                )
                self.assertEqual(product.category.magento_ids[0].magento_id, 8)
                self.assertEqual(
                    product.channel_listings[0].magento_product_type, 'simple'
                )
                self.assertEqual(product.name, 'BlackBerry 8100 Pearl')

                products_after_import = Product.search([], count=True)
                self.assertTrue(products_after_import > products_before_import)

                self.assertEqual(
                    product,
                    Product.find_using_magento_data(
                        product_data
                    )
                )

                # Make sure the categs are created only in channel1 and not
                # not in channel2
                self.assertTrue(ProductSaleChannelListing.search(
                    [('channel', '=', self.channel1)],
                    count=True) > 0
                )
                self.assertTrue(ProductSaleChannelListing.search(
                    [('channel', '=', self.channel2)],
                    count=True) == 0
                )

    def test_0300_import_product_wo_categories(self):
        """
        Test the import of a product using magento data which doesn't
        have categories
        """
        Product = POOL.get('product.product')

        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            self.setup_defaults()
            product_data = load_json('products', '17-wo-category')
            with txn.set_context({
                'current_channel': self.channel1.id,
                'company': self.company.id,
            }):
                product = Product.find_or_create_using_magento_data(
                    product_data
                )
                self.assertEqual(
                    product.channel_listings[0].magento_product_type, 'simple'
                )
                self.assertEqual(product.name, 'BlackBerry 8100 Pearl')
                self.assertEqual(
                    product.category.name, 'Unclassified Magento Products'
                )

    def test_0040_import_configurable_product(self):
        """
        Test the import of a configurable product using Magento Data
        """
        Category = POOL.get('product.category')
        Product = POOL.get('product.product')

        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            self.setup_defaults()
            category_data = load_json('categories', '17')
            product_data = load_json('products', '135')

            with txn.set_context({
                'current_channel': self.channel1.id,
                'company': self.company.id,
            }):
                Category.create_using_magento_data(category_data)
                product = Product.find_or_create_using_magento_data(
                    product_data
                )
                self.assertEqual(
                    product.category.magento_ids[0].magento_id, 17
                )
                self.assertEqual(
                    product.channel_listings[0].magento_product_type,
                    'configurable'
                )

    def test_0050_import_grouped_product(self):
        """
        Test the import of a grouped product using magento data
        """
        Category = POOL.get('product.category')
        Product = POOL.get('product.product')

        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            self.setup_defaults()
            category_data = load_json('categories', 22)
            product_data = load_json('products', 54)
            with txn.set_context({
                'current_channel': self.channel1.id,
                'company': self.company.id,
            }):
                Category.create_using_magento_data(category_data)
                product = Product.find_or_create_using_magento_data(
                    product_data
                )
                self.assertEqual(
                    product.category.magento_ids[0].magento_id, 22
                )
                self.assertEqual(
                    product.channel_listings[0].magento_product_type,
                    'grouped'
                )

    def test_0060_import_downloadable_product(self):
        """
        Test the import of a downloadable product using magento data
        """
        Product = POOL.get('product.product')

        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            self.setup_defaults()
            product_data = load_json('products', '170')
            with txn.set_context({
                'current_channel': self.channel1.id,
                'company': self.company.id,
            }):
                product = Product.find_or_create_using_magento_data(
                    product_data
                )
                self.assertEqual(
                    product.channel_listings[0].magento_product_type,
                    'downloadable'
                )
                self.assertEqual(
                    product.category.name,
                    'Unclassified Magento Products'
                )

    def test_0070_update_product_using_magento_data(self):
        """
        Check if the product template gets updated using magento data
        """
        Product = POOL.get('product.product')
        Category = POOL.get('product.category')

        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.setup_defaults()

            with Transaction().set_context({
                'current_channel': self.channel1.id,
                'company': self.company.id,
            }):

                category_data = load_json('categories', '17')

                Category.create_using_magento_data(category_data)

                product_data = load_json('products', '135')

                product1 = \
                    Product.find_or_create_using_magento_data(
                        product_data
                    )

                product_id_before_updation = product1.id
                product_name_before_updation = product1.name
                product_code_before_updation = \
                    product1.products[0].code
                product_description_before_updation = \
                    product1.products[0].description

                # Use a JSON file with product name, code and description
                # changed and everything else same
                product_data = load_json('products', '135001')
                product2 = \
                    product1.update_from_magento_using_data(
                        product_data
                    )

                self.assertEqual(
                    product_id_before_updation, product2.id
                )
                self.assertNotEqual(
                    product_name_before_updation,
                    product2.name
                )
                self.assertNotEqual(
                    product_code_before_updation,
                    product2.products[0].code
                )
                self.assertNotEqual(
                    product_description_before_updation,
                    product2.products[0].description
                )

    def test_0103_update_product_using_magento_id(self):
        """
        Check if the product template gets updated using magento ID
        """
        Product = POOL.get('product.product')
        Category = POOL.get('product.category')

        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.setup_defaults()
            with Transaction().set_context({
                'current_channel': self.channel1.id,
                'company': self.company.id,
            }):

                category_data = load_json('categories', '17')

                Category.create_using_magento_data(category_data)

                product_data = load_json('products', '135001')
                product1 = \
                    Product.find_or_create_using_magento_data(
                        product_data
                    )

                product_id_before_updation = product1.id
                product_name_before_updation = product1.name
                product_code_before_updation = \
                    product1.products[0].code
                product_description_before_updation = \
                    product1.products[0].description

                # Use a JSON file with product name, code and description
                # changed and everything else same
                with patch('magento.Product', mock_product_api(), create=True):
                    product2 = product1.update_from_magento()

                self.assertEqual(
                    product_id_before_updation, product2.id
                )
                self.assertNotEqual(
                    product_name_before_updation,
                    product2.name
                )
                self.assertNotEqual(
                    product_code_before_updation,
                    product2.products[0].code
                )
                self.assertNotEqual(
                    product_description_before_updation,
                    product2.products[0].description
                )

    def test_0080_export_product_stock_information(self):
        """
        This test checks if the method to call for updation of product
        stock info does not break anywhere in between.
        This method does not check the API calls
        """
        Product = POOL.get('product.product')
        Category = POOL.get('product.category')

        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.setup_defaults()

            with Transaction().set_context({
                'current_channel': self.channel1.id,
                'company': self.company.id,
            }):

                category_data = load_json('categories', '17')

                Category.create_using_magento_data(category_data)

                product_data = load_json('products', '135')
                Product.find_or_create_using_magento_data(
                    product_data
                )

                with patch(
                    'magento.Inventory', mock_inventory_api(), create=True
                ):
                    self.channel1.export_inventory_to_magento()

    def test_0090_tier_prices(self):
        """Checks the function field on product price tiers
        """
        PriceList = POOL.get('product.price_list')
        ProductPriceTier = POOL.get('product.price_tier')
        Product = POOL.get('product.product')
        Category = POOL.get('product.category')
        User = POOL.get('res.user')

        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            self.setup_defaults()
            context = User.get_preferences(context_only=True)
            context.update({
                'current_channel': self.channel1.id,
                'company': self.company.id,
            })
            with txn.set_context(context):
                category_data = load_json('categories', '17')
                Category.create_using_magento_data(category_data)

                product_data = load_json('products', '135')
                product = \
                    Product.find_or_create_using_magento_data(
                        product_data
                    )

                price_list, = PriceList.create([{
                    'name': 'Test Pricelist',
                    'lines': [('create', [{
                        'quantity': 10,
                        'formula': 'unit_price*0.9'
                    }])]
                }])
                self.channel1.price_list = price_list
                self.channel1.save()

                tier, = ProductPriceTier.create([{
                    'template': product.id,
                    'quantity': 10,
                }])

                self.assertEqual(
                    product.list_price * Decimal('0.9'), tier.price
                )

    def test_0110_export_catalog(self):
        """
        Check the export of product catalog to magento.
        This method does not check the API calls.
        """
        ProductTemplate = POOL.get('product.template')
        Category = POOL.get('product.category')
        Uom = POOL.get('product.uom')

        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            self.setup_defaults()

            with txn.set_context({
                'current_channel': self.channel1.id,
                'magento_attribute_set': 1,
                'company': self.company.id,
            }):
                category_data = load_json('categories', '17')
                category = Category.create_using_magento_data(category_data)

                uom, = Uom.search([('name', '=', 'Unit')], limit=1)
                product_template, = ProductTemplate.create([
                    {
                        'name': 'Test product',
                        'list_price': Decimal('100'),
                        'cost_price': Decimal('1'),
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

                with patch(
                    'magento.Product', mock_product_api(), create=True
                ):
                    product_template.products[0].export_to_magento(category)


def suite():
    """Test Suite"""
    _suite = trytond.tests.test_tryton.suite()
    _suite.addTests([
        unittest.TestLoader().loadTestsFromTestCase(TestProduct),
    ])
    return _suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
