# -*- coding: UTF-8 -*-
'''
    product

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
'''
import magento
from trytond.model import ModelSQL, ModelView, fields
from trytond.transaction import Transaction
from trytond.pool import PoolMeta, Pool
from decimal import Decimal


__all__ = ['Category', 'MagentoInstanceCategory']
__metaclass__ = PoolMeta


class Category:
    "Product Category"
    __name__ = "product.category"

    magento_ids = fields.One2Many(
        'magento.instance.product_category', 'category',
        'Magento IDs', readonly=True,
    )

    @classmethod
    def create_tree_using_magento_data(cls, category_tree):
        """
        Create the categories from the category tree

        :param category_tree: Category Tree from Magento
        """
        #Create the root
        root_category = cls.find_or_create_using_magento_data(
            category_tree
        )
        for child in category_tree['children']:
            cls.find_or_create_using_magento_data(
                child, parent=root_category
            )
            if child['children']:
                cls.create_tree_using_magento_data(child)

    @classmethod
    def find_or_create_using_magento_data(
        cls, category_data, parent=None
    ):
        """
        Find or Create category using Magento Database

        :param category_data: Category Data from Magento
        :param parent: Browse record of Parent if present, else None
        :returns: Active record of category found/created
        """
        category = cls.find_using_magento_data(
            category_data
        )

        if not category:
            category = cls.create_using_magento_data(
                category_data, parent
            )
        return category

    @classmethod
    def find_or_create_using_magento_id(
        cls, magento_id, parent=None
    ):
        """
        Find or Create Category Using Magento ID of Category

        :param category_data: Category Data from Magento
        :param parent: Browse record of Parent if present, else None
        :returns: Active record of category found/created
        """
        Instance = Pool().get('magento.instance')

        category = cls.find_using_magento_id(magento_id)
        if not category:
            instance = Instance(
                Transaction().context.get('magento_instance')
            )

            with magento.Category(
                instance.url, instance.api_user, instance.api_key
            ) as category_api:
                category_data = category_api.info(magento_id)

            category = cls.create_using_magento_data(
                category_data, parent
            )

        return category

    @classmethod
    def find_using_magento_data(cls, category_data):
        """
        Find category using Magento Data

        :param category_data: Category Data from Magento
        :returns: Active record of category found or None
        """
        MagentoCategory = Pool().get('magento.instance.product_category')

        records = MagentoCategory.search([
            ('magento_id', '=', int(category_data['category_id'])),
            ('instance', '=', Transaction().context.get('magento_instance'))
        ])
        return records and records[0].category or None

    @classmethod
    def find_using_magento_id(cls, magento_id):
        """
        Find category using Magento ID or Category

        :param magento_id: Category ID from Magento
        :type magento_id: Integer
        :returns: Active record of Category Found or None
        """
        MagentoCategory = Pool().get('magento.instance.product_category')

        records = MagentoCategory.search([
            ('magento_id', '=', magento_id),
            ('instance', '=', Transaction().context.get('magento_instance'))
        ])

        return records and records[0].category or None

    @classmethod
    def create_using_magento_data(cls, category_data, parent=None):
        """
        Create category using magento data

        :param category_data: Category Data from magento
        :param parent: Browse record of Parent if present, else None
        :returns: Active record of category created
        """

        category, = cls.create([{
            'name': category_data['name'],
            'parent': parent,
            'magento_ids': [('create', [{
                'magento_id': int(category_data['category_id']),
                'instance': Transaction().context.get('magento_instance'),
            }])]
        }])

        return category


class MagentoInstanceCategory(ModelSQL, ModelView):
    """
    Magento Instance - Product Category Store

    This model keeps a record of a category's association with an Instance
    and the ID of the category on that instance
    """
    __name__ = "magento.instance.product_category"

    magento_id = fields.Integer(
        'Magento ID', readonly=True, required=True, select=True
    )
    instance = fields.Many2One(
        'magento.instance', 'Magento Instance', readonly=True,
        required=True, select=True
    )
    category = fields.Many2One(
        'product.category', 'Product Category', readonly=True,
        required=True, select=True
    )

    @classmethod
    def __setup__(cls):
        '''
        Setup the class and define constraints
        '''
        super(MagentoInstanceCategory, cls).__setup__()
        cls._sql_constraints += [
            (
                'magento_id_instance_unique',
                'UNIQUE(magento_id, instance)',
                'Each category in an instance must be unique!'
            )
        ]


class Template:
    "Product Template"

    __name__ = "product.template"

    magento_product_type = fields.Selection([
        ('simple', 'Simple'),
        ('configurable', 'Configurable'),
        ('grouped', 'Grouped'),
        ('bundle', 'Bundle'),
        ('virtual', 'Virtual'),
        ('downloadable', 'Downloadable'),
    ], 'Magento Product Type', readonly=True)
    magento_ids = fields.One2Many(
        'magento.website.template', 'template',
        'Magento IDs', readonly=True
    )

    @classmethod
    def find_or_create_using_magento_id(cls, magento_id):
        """
        Find or create a product template using magento ID. This method looks
        for an existing template using the magento ID provided. If found, it
        returns the template found, else creates a new one and returns that

        :param magento_id: Product ID from Magento
        :returns: Active record of Product Created
        """
        Website = Pool().get('magento.instance.website')

        product = cls.find_using_magento_id(magento_id)

        if not product:
            # if product is not found get the info from magento and
            # delegate to create_using_magento_data
            website = Website(Transaction().context.get('magento_website'))

            instance = website.instance
            with magento.Product(
                    instance.url, instance.api_user, instance.api_key
            ) as product_api:
                product_data = product_api.info(magento_id)

            product = cls.create_using_magento_data(product_data)

        return product

    @classmethod
    def find_using_magento_id(cls, magento_id):
        """
        Find a product template corresponding to the magento ID provided. If
        found return that else None

        :param magento_id: Product ID from Magento
        :returns: Product created for the Record
        """
        MagentoTemplate = Pool().get('magento.website.template')

        records = MagentoTemplate.search([
            ('magento_id', '=', magento_id),
            ('website', '=', Transaction().context.get('magento_website'))
        ])

        return records and records[0].template or None

    @classmethod
    def find_or_create_using_magento_data(cls, product_data):
        """
        Find or create a product template using magento data provided.
        This method looks for an existing template using the magento ID From
        data provided. If found, it returns the template found, else creates
        a new one and returns that

        :param product_data: Product Data From Magento
        :returns: Browse record of product found/created
        """
        template = cls.find_using_magento_data(product_data)

        if not template:
            template = cls.create_using_magento_data(product_data)

        return template

    @classmethod
    def find_using_magento_data(cls, product_data):
        """
        Find a product template corresponding to the magento data provided.
        If found return that else None

        :param product_data: Category Data from Magento
        :returns: Browse record of product found or None
        """
        MagentoTemplate = Pool().get('magento.website.template')

        records = MagentoTemplate.search([
            ('magento_id', '=', int(product_data['product_id'])),
            ('website', '=', Transaction().context.get('magento_website'))
        ])
        return records and records[0].template or None

    @classmethod
    def extract_product_values_from_data(cls, product_data):
        """
        Extract product values from the magento data, used for both
        creation/updation of product. This method can be overwritten by
        custom modules to store extra info to a product

        :param: product_data
        :returns: Dictionary of values
        """
        Website = Pool().get('magento.instance.website')

        website = Website(Transaction().context.get('magento_website'))
        return {
            'name': product_data['name'],
            'list_price': Decimal(
                product_data.get('special_price') or
                product_data.get('price') or
                0.00
            ),
            'cost_price': Decimal(product_data.get('price') or 0.00),
            'default_uom': website.default_uom.id,
            'products': [('create', [{
                'description': product_data['description'],
                'code': product_data['sku'],
            }])]
        }

    @classmethod
    def create_using_magento_data(cls, product_data):
        """
        Create a new product with the `product_data` from magento.This method
        also looks for the category of the product. If found, it uses that
        category to assign the product to. If no category is found, it assigns
        the product to `Unclassified Magento Product` category

        :param product_data: Product Data from Magento
        :returns: Browse record of product created
        """
        Category = Pool().get('product.category')

        # Get only the first category from the list of categories
        # If no category is found, put product under unclassified category
        # which is created by default data
        if product_data.get('categories'):
            category = Category.find_or_create_using_magento_id(
                int(product_data['categories'][0])
            )
        else:
            categories = Category.search([
                ('name', '=', 'Unclassified Magento Products')
            ])
            category = categories[0]

        product_values = cls.extract_product_values_from_data(
            product_data
        )
        product_values.update({
            'category': category.id,
            'magento_product_type': product_data['type'],
            'magento_ids': [('create', [{
                'magento_id': int(product_data['product_id']),
                'website': Transaction().context.get('magento_website'),
            }])],
        })

        product, = cls.create([product_values])

        return product


class MagentoWebsiteTemplate(ModelSQL, ModelView):
    """
    Magento Website ---  Product Template Store

    This model keeps a record of a product's association with a website and
    the ID of product on that website
    """
    __name__ = 'magento.website.template'

    magento_id = fields.Integer(
        'Magento ID', readonly=True, required=True, select=True
    )
    website = fields.Many2One(
        'magento.instance.website', 'Magento Website', readonly=True,
        select=True, required=True
    )
    template = fields.Many2One(
        'product.template', 'Template', readonly=True,
        required=True, select=True
    )

    @classmethod
    def __setup__(cls):
        '''
        Setup the class and define constraints
        '''
        super(MagentoWebsiteTemplate, cls).__setup__()
        cls._sql_constraints += [
            (
                'magento_id_website_unique',
                'UNIQUE(magento_id, website)',
                'Each product in an instance must be unique!'
            )
        ]
