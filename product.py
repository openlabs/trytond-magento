# -*- coding: UTF-8 -*-
'''
    product

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
'''
import magento
from trytond.model import ModelSQL, ModelView, fields
from trytond.transaction import Transaction
from trytond.wizard import Wizard, StateView, StateAction, Button
from trytond.pyson import PYSONEncoder
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

        product_template = cls.find_using_magento_id(magento_id)

        if not product_template:
            # if product is not found get the info from magento and
            # delegate to create_using_magento_data
            website = Website(Transaction().context.get('magento_website'))

            instance = website.instance
            with magento.Product(
                    instance.url, instance.api_user, instance.api_key
            ) as product_api:
                product_data = product_api.info(magento_id)

            product_template = cls.create_using_magento_data(product_data)

        return product_template

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
        product_template = cls.find_using_magento_data(product_data)

        if not product_template:
            product_template = cls.create_using_magento_data(product_data)

        return product_template

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

        product_template_values = cls.extract_product_values_from_data(
            product_data
        )
        product_template_values.update({
            'products': [('create', [{
                'description': product_data['description'],
                'code': product_data['sku'],
            }])],
            'category': category.id,
            'magento_product_type': product_data['type'],
            'magento_ids': [('create', [{
                'magento_id': int(product_data['product_id']),
                'website': Transaction().context.get('magento_website'),
            }])],
        })

        product, = cls.create([product_template_values])

        return product

    def update_from_magento(self):
        """
        Update product using magento ID for that product

        :returns: Active record of product updated
        """
        Website = Pool().get('magento.instance.website')
        MagentoProductTemplate = Pool().get('magento.website.template')

        website = Website(Transaction().context.get('magento_website'))
        instance = website.instance

        with magento.Product(
            instance.url, instance.api_user, instance.api_key
        ) as product_api:
            magento_product_template, = MagentoProductTemplate.search([
                ('template', '=', self.id),
                ('website', '=', website.id),
            ])
            product_data = product_api.info(
                magento_product_template.magento_id
            )

        return self.update_from_magento_using_data(product_data)

    def update_from_magento_using_data(self, product_data):
        """
        Update product using magento data

        :param product_data: Product Data from magento
        :returns: Active record of product updated
        """
        product_template_values = self.extract_product_values_from_data(
            product_data
        )
        product_template_values.update({
            'products': [('write', map(int, self.products), {
                'description': product_data['description'],
                'code': product_data['sku'],
            })]
        })
        self.write([self], product_template_values)

        return self


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

        cls._buttons.update({
            'update_product_from_magento': {},
        })

    @classmethod
    def update_product_from_magento(cls, magento_product_templates):
        """
        Update the product from magento with the details from magento
        for the current website

        :param magento_product_templates: List of active record of magento
                                          product templates
        """
        for magento_product_template in magento_product_templates:
            with Transaction().set_context({
                    'magento_website': magento_product_template.website.id}):
                magento_product_template.template.update_from_magento()

        return {}


class UpdateCatalogStart(ModelView):
    'Update Catalog View'
    __name__ = 'magento.instance.update_catalog.start'


class UpdateCatalog(Wizard):
    '''
    Update Catalog

    This is a wizard to update already imported products
    '''
    __name__ = 'magento.instance.update_catalog'

    start = StateView(
        'magento.instance.update_catalog.start',
        'magento.update_catalog_start', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Continue', 'update_', 'tryton-ok', default=True),
        ]
    )
    update_ = StateAction('product.act_template_form')

    def do_update_(self, action):
        """Handles the transition"""

        Website = Pool().get('magento.instance.website')

        website = Website(Transaction().context.get('active_id'))

        product_template_ids = self.update_products(website)

        action['pyson_domain'] = PYSONEncoder().encode(
            [('id', 'in', product_template_ids)])
        return action, {}

    def transition_import_(self):
        return 'end'

    def update_products(self, website):
        """
        Updates products for current website

        :param website: Browse record of website
        :return: List of product templates IDs
        """
        product_templates = []
        with Transaction().set_context({'magento_website': website.id}):
            for mag_product_template in website.magento_product_templates:
                product_templates.append(
                    mag_product_template.template.update_from_magento()
                )

        return map(int, product_templates)


class ImportCatalogStart(ModelView):
    'Import Catalog View'
    __name__ = 'magento.instance.import_catalog.start'


class ImportCatalog(Wizard):
    '''
    Import Catalog

    This is a wizard to import Products from a Magento Website. It opens up
    the list of products after the import has been completed.
    '''
    __name__ = 'magento.instance.import_catalog'

    start = StateView(
        'magento.instance.import_catalog.start',
        'magento.instance_import_catalog_start', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Continue', 'import_', 'tryton-ok', default=True),
        ]
    )
    import_ = StateAction('product.act_template_form')

    def do_import_(self, action):
        """Handles the transition"""

        Website = Pool().get('magento.instance.website')

        website = Website(Transaction().context.get('active_id'))

        self.import_category_tree(website)
        product_ids = self.import_products(website)
        action['pyson_domain'] = PYSONEncoder().encode(
            [('id', 'in', product_ids)])
        return action, {}

    def transition_import_(self):
        return 'end'

    def import_category_tree(self, website):
        """
        Imports the category tree and creates categories in a hierarchy same as
        that on Magento

        :param website: Active record of website
        """
        Category = Pool().get('product.category')

        instance = website.instance
        Transaction().set_context({'magento_instance': instance.id})

        with magento.Category(
            instance.url, instance.api_user, instance.api_key
        ) as category_api:
            category_tree = category_api.tree(website.magento_root_category_id)
            Category.create_tree_using_magento_data(category_tree)

    def import_products(self, website):
        """
        Imports products for the current instance

        :param website: Active record of website
        """
        Product = Pool().get('product.template')

        instance = website.instance
        Transaction().set_context({
            'magento_instance': instance.id,
            'magento_website': website.id
        })
        with magento.Product(
            instance.url, instance.api_user, instance.api_key
        ) as product_api:
            magento_products = []
            products = []

            # Products are linked to websites. But the magento api filters
            # the products based on store views. The products available on
            # website are always available on all of its store views.
            # So we get one store view for each website in current instance.
            magento_products.extend(
                product_api.list(
                    store_view=website.stores[0].store_views[0].magento_id
                )
            )

            for magento_product in magento_products:
                products.append(
                    Product.find_or_create_using_magento_id(
                        magento_product['product_id']
                    )
                )

        return map(int, products)
