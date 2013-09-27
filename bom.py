# -*- coding: utf-8 -*-
"""
    bom

    BOM

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
from trytond.pool import Pool, PoolMeta


__all__ = ['BOM']
__metaclass__ = PoolMeta


class BOM:
    "Bill of Material"
    __name__ = 'production.bom'

    @classmethod
    def identify_boms_from_magento_data(cls, order_data):
        """
        Create a dict of bundle product data for use in creation of bom

        :param order_data: Order data sent from magento
        :return: Dictionary in format
            {
                <item_id of bundle product>: {
                    'bundle': <item data for bundle product>,
                    'components': [<item data>, <item data>]
                }
            }
        """
        bundles = {}

        # Identify all the bundles in the order
        for item in order_data['items']:
            # Iterate over each item in order items
            if item['product_type'] == 'bundle' and not item['parent_item_id']:
                # If product_type is bundle and does not have a parent(obvious)
                # then create a new entry in bundle_products
                # .. note:: item_id is the unique ID of each order line
                bundles[item['item_id']] = {'bundle': item, 'components': []}

        # Identify and add components
        for item in order_data['items']:
            if item['product_type'] != 'bundle' and \
                    'bundle_option' in item['product_options'] and \
                    item['parent_item_id']:

                bundles[item['parent_item_id']]['components'].append(item)

        return bundles

    @classmethod
    def find_or_create_bom_for_magento_bundle(cls, order_data):
        """
        Find or create a BoM for bundle product from the data sent in
        magento order

        :param order_data: Order Data from magento
        :return: Found or created BoM's active record
        """
        Uom = Pool().get('product.uom')
        ProductTemplate = Pool().get('product.template')
        ProductBom = Pool().get('product.product-production.bom')

        identified_boms = cls.identify_boms_from_magento_data(order_data)

        if not identified_boms:
            return

        for item_id, data in identified_boms.iteritems():
            bundle_product_template = \
                ProductTemplate.find_or_create_using_magento_id(
                    data['bundle']['product_id']
                )
            bundle_product = bundle_product_template.products[0]

            # It contains a list of tuples, in which the first element is the
            # product's active record and second is its quantity in the BoM
            child_products = [(
                ProductTemplate.find_or_create_using_magento_id(
                    each['product_id']
                ).products[0], (
                    float(each['qty_ordered']) /
                    float(data['bundle']['qty_ordered'])
                )
            ) for each in data['components']]

            # Here we match the sets of BoM components for equality
            # Each set contains tuples of product and quantity of that
            # product in the BoM
            # If everything for a BoM matches, then we dont create a new one
            # and use this BoM itself
            # XXX This might eventually have issues because of rounding
            # in quantity
            for product_bom in bundle_product.boms:
                existing_bom_set = set([
                    (input.product.id, input.quantity)
                    for input in product_bom.bom.inputs
                ])
                new_bom_set = set([
                    (product.id, qty) for product, qty in child_products
                ])
                if existing_bom_set == new_bom_set:
                    break
            else:
                # No matching BoM found, create a new one
                unit, = Uom.search([('name', '=', 'Unit')])
                bom, = cls.create([{
                    'name': bundle_product.name,
                    'inputs': [('create', [{
                        'uom': unit.id,
                        'product': product.id,
                        'quantity': quantity,
                    }]) for product, quantity in child_products],
                    'outputs': [('create', [{
                        'uom': unit,
                        'product': bundle_product.id,
                        'quantity': bundle_product.quantity,
                    }])]
                }])

                product_bom = ProductBom.create([{
                    'product': bundle_product.id,
                    'bom': bom.id,
                }])

        return product_bom
