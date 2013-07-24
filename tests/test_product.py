# -*- coding: utf-8 -*-
"""
    test_product

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
from trytond.tests.test_tryton import POOL, USER, DB_NAME, CONTEXT
from test_base import TestBase, load_json
from trytond.transaction import Transaction


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


def suite():
    """Test Suite"""
    _suite = trytond.tests.test_tryton.suite()
    _suite.addTests([
        unittest.TestLoader().loadTestsFromTestCase(TestProduct),
    ])
    return _suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
