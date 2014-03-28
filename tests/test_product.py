# -*- coding: utf-8 -*-
"""
    test_product

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
import magento
from mock import patch, MagicMock

import trytond.tests.test_tryton
from trytond.tests.test_tryton import POOL, USER, DB_NAME, CONTEXT
from test_base import TestBase, load_json
from trytond.transaction import Transaction


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
            with txn.set_context({'magento_instance': self.instance1.id}):
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
                        ('instance', '=', self.instance1)
                    ], count=True) > 0
                )
                self.assertTrue(
                    MagentoCategory.search([
                        ('instance', '=', self.instance2)
                    ], count=True) == 0
                )

    def test_0020_import_simple_product(self):
        """
        Test the import of simple product using Magento Data
        """
        Category = POOL.get('product.category')
        ProductTemplate = POOL.get('product.template')
        MagentoTemplate = POOL.get('magento.website.template')

        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            self.setup_defaults()

            category_data = load_json('categories', '8')

            with txn.set_context({
                'magento_instance': self.instance1,
                'magento_website': self.website1,
                'company': self.company,
            }):
                Category.create_using_magento_data(category_data)

                products_before_import = ProductTemplate.search([], count=True)

                product_data = load_json('products', '17')
                template = ProductTemplate.find_or_create_using_magento_data(
                    product_data
                )
                self.assertEqual(template.category.magento_ids[0].magento_id, 8)
                self.assertEqual(template.magento_product_type, 'simple')
                self.assertEqual(template.name, 'BlackBerry 8100 Pearl')

                products_after_import = ProductTemplate.search([], count=True)
                self.assertTrue(products_after_import > products_before_import)

                self.assertEqual(
                    template,
                    ProductTemplate.find_using_magento_data(
                        product_data
                    )
                )

                # Make sure the categs are created only in website1 and not
                # not in website2
                self.assertTrue(MagentoTemplate.search(
                    [('website', '=', self.website1)],
                    count=True) > 0
                )
                self.assertTrue(MagentoTemplate.search(
                    [('website', '=', self.website2)],
                    count=True) == 0
                )

    def test_0300_import_product_wo_categories(self):
        """
        Test the import of a product using magento data which doesn't
        have categories
        """
        ProductTemplate = POOL.get('product.template')

        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            self.setup_defaults()
            product_data = load_json('products', '17-wo-category')
            with txn.set_context({
                'magento_instance': self.instance1,
                'magento_website': self.website1,
                'company': self.company,
            }):
                template = ProductTemplate.find_or_create_using_magento_data(
                    product_data
                )
                self.assertEqual(template.magento_product_type, 'simple')
                self.assertEqual(template.name, 'BlackBerry 8100 Pearl')
                self.assertEqual(
                    template.category.name, 'Unclassified Magento Products'
                )

    def test_0040_import_configurable_product(self):
        """
        Test the import of a configurable product using Magento Data
        """
        Category = POOL.get('product.category')
        ProductTemplate = POOL.get('product.template')

        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            self.setup_defaults()
            category_data = load_json('categories', '17')
            product_data = load_json('products', '135')

            with txn.set_context({
                'magento_instance': self.instance1,
                'magento_website': self.website1,
                'company': self.company,
            }):
                Category.create_using_magento_data(category_data)
                template = ProductTemplate.find_or_create_using_magento_data(
                    product_data
                )
                self.assertEqual(
                    template.category.magento_ids[0].magento_id, 17
                )
                self.assertEqual(
                    template.magento_product_type, 'configurable'
                )

    def test_0050_import_grouped_product(self):
        """
        Test the import of a grouped product using magento data
        """
        Category = POOL.get('product.category')
        ProductTemplate = POOL.get('product.template')

        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            self.setup_defaults()
            category_data = load_json('categories', 22)
            product_data = load_json('products', 54)
            with txn.set_context({
                'magento_instance': self.instance1,
                'magento_website': self.website1,
                'company': self.company,
            }):
                Category.create_using_magento_data(category_data)
                template = ProductTemplate.find_or_create_using_magento_data(
                    product_data
                )
                self.assertEqual(
                    template.category.magento_ids[0].magento_id, 22
                )
                self.assertEqual(
                    template.magento_product_type, 'grouped'
                )

    def test_0060_import_downloadable_product(self):
        """
        Test the import of a downloadable product using magento data
        """
        ProductTemplate = POOL.get('product.template')

        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            self.setup_defaults()
            product_data = load_json('products', '170')
            with txn.set_context({
                'magento_instance': self.instance1,
                'magento_website': self.website1,
                'company': self.company,
            }):
                template = ProductTemplate.find_or_create_using_magento_data(
                    product_data
                )
                self.assertEqual(template.magento_product_type, 'downloadable')
                self.assertEqual(
                    template.category.name,
                    'Unclassified Magento Products'
                )

    def test_0070_update_product_using_magento_data(self):
        """
        Check if the product template gets updated using magento data
        """
        ProductTemplate = POOL.get('product.template')
        Category = POOL.get('product.category')

        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.setup_defaults()

            with Transaction().set_context({
                'magento_instance': self.instance1.id,
                'magento_website': self.website1.id,
                'magento_store': self.store,
                'company': self.company,
            }):

                category_data = load_json('categories', '17')

                Category.create_using_magento_data(category_data)

                product_data = load_json('products', '135')

                product_template1 = \
                    ProductTemplate.find_or_create_using_magento_data(
                        product_data
                    )

                product_template_id_before_updation = product_template1.id
                product_template_name_before_updation = product_template1.name
                product_code_before_updation = \
                    product_template1.products[0].code
                product_description_before_updation = \
                    product_template1.products[0].description

                # Use a JSON file with product name, code and description
                # changed and everything else same
                product_data = load_json('products', '135001')
                product_template2 = \
                    product_template1.update_from_magento_using_data(
                        product_data
                    )

                self.assertEqual(
                    product_template_id_before_updation, product_template2.id
                )
                self.assertNotEqual(
                    product_template_name_before_updation,
                    product_template2.name
                )
                self.assertNotEqual(
                    product_code_before_updation,
                    product_template2.products[0].code
                )
                self.assertNotEqual(
                    product_description_before_updation,
                    product_template2.products[0].description
                )

    def test_0103_update_product_using_magento_id(self):
        """
        Check if the product template gets updated using magento ID
        """
        ProductTemplate = POOL.get('product.template')
        Category = POOL.get('product.category')

        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.setup_defaults()
            with Transaction().set_context({
                'magento_instance': self.instance1.id,
                'magento_website': self.website1.id,
                'magento_store': self.store,
                'company': self.company,
            }):

                category_data = load_json('categories', '17')

                Category.create_using_magento_data(category_data)

                product_data = load_json('products', '135001')
                product_template1 = \
                    ProductTemplate.find_or_create_using_magento_data(
                        product_data
                    )

                product_template_id_before_updation = product_template1.id
                product_template_name_before_updation = product_template1.name
                product_code_before_updation = \
                    product_template1.products[0].code
                product_description_before_updation = \
                    product_template1.products[0].description

                # Use a JSON file with product name, code and description
                # changed and everything else same
                with patch('magento.Product', mock_product_api(), create=True):
                    product_template2 = product_template1.update_from_magento()

                self.assertEqual(
                    product_template_id_before_updation, product_template2.id
                )
                self.assertNotEqual(
                    product_template_name_before_updation,
                    product_template2.name
                )
                self.assertNotEqual(
                    product_code_before_updation,
                    product_template2.products[0].code
                )
                self.assertNotEqual(
                    product_description_before_updation,
                    product_template2.products[0].description
                )

    def test_0080_export_product_stock_information(self):
        """
        This test checks if the method to call for updation of product
        stock info does not break anywhere in between.
        This method does not check the API calls
        """
        ProductTemplate = POOL.get('product.template')
        Category = POOL.get('product.category')

        with Transaction().start(DB_NAME, USER, CONTEXT):
            self.setup_defaults()

            with Transaction().set_context({
                'magento_instance': self.instance1.id,
                'magento_website': self.website1.id,
                'company': self.company,
            }):

                category_data = load_json('categories', '17')

                Category.create_using_magento_data(category_data)

                product_data = load_json('products', '135')
                ProductTemplate.find_or_create_using_magento_data(
                    product_data
                )

                with patch(
                    'magento.Inventory', mock_inventory_api(), create=True
                ):
                    self.website1.export_inventory_to_magento()

    def test_0090_tier_prices(self):
        """Checks the function field on product price tiers
        """
        Store = POOL.get('magento.website.store')
        PriceList = POOL.get('product.price_list')
        ProductPriceTier = POOL.get('product.price_tier')
        ProductTemplate = POOL.get('product.template')
        Category = POOL.get('product.category')
        User = POOL.get('res.user')

        with Transaction().start(DB_NAME, USER, CONTEXT) as txn:
            self.setup_defaults()
            context = User.get_preferences(context_only=True)
            context.update({
                'magento_instance': self.instance1.id,
                'magento_website': self.website1.id,
                'magento_store': self.store.id,
                'company': self.company.id,
            })
            with txn.set_context(context):
                category_data = load_json('categories', '17')
                Category.create_using_magento_data(category_data)

                product_data = load_json('products', '135')
                product_template = \
                    ProductTemplate.find_or_create_using_magento_data(
                        product_data
                    )

                price_list, = PriceList.create([{
                    'name': 'Test Pricelist',
                    'lines': [('create', [{
                        'quantity': 10,
                        'formula': 'unit_price*0.9'
                    }])]
                }])
                Store.write([self.store], {'price_list': price_list.id})

                tier, = ProductPriceTier.create([{
                    'template': product_template.id,
                    'quantity': 10,
                }])

                self.assertEqual(
                    product_template.list_price * Decimal('0.9'), tier.price
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
                'magento_instance': self.instance1.id,
                'magento_website': self.website1.id,
                'magento_attribute_set': 1,
                'company': self.company.id,
            }):
                category_data = load_json('categories', '17')
                category = Category.create_using_magento_data(category_data)

                uom, = Uom.search([('name', '=', 'Unit')], limit=1)
                product, = ProductTemplate.create([
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
                    product.export_to_magento(category)


def suite():
    """Test Suite"""
    _suite = trytond.tests.test_tryton.suite()
    _suite.addTests([
        unittest.TestLoader().loadTestsFromTestCase(TestProduct),
    ])
    return _suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
