# -*- coding: utf-8 -*-
"""
    magento_

    Magento

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
import xmlrpclib
import socket

import magento
from trytond.model import ModelView, ModelSQL, fields
from trytond.pool import PoolMeta, Pool
from trytond.transaction import Transaction
from trytond.pyson import PYSONEncoder
from trytond.wizard import Wizard, StateView, Button, StateAction
from .api import OrderConfig

from .api import Core


__all__ = [
    'Instance', 'InstanceWebsite', 'WebsiteStore', 'WebsiteStoreView',
    'TestConnectionStart', 'TestConnection', 'ImportWebsitesStart',
    'ImportWebsites', 'ExportInventoryStart', 'ExportInventory'
]
__metaclass__ = PoolMeta


class Instance(ModelSQL, ModelView):
    """
    Magento Instance

    Refers to a magento installation identifiable via url, api_user and api_key
    """
    __name__ = 'magento.instance'

    name = fields.Char("Name", required=True)
    url = fields.Char("Magento Site URL", required=True)
    api_user = fields.Char("API User", required=True)
    api_key = fields.Char("API Key", required=True)
    active = fields.Boolean("Active")
    company = fields.Many2One("company.company", "Company", required=True)
    websites = fields.One2Many(
        "magento.instance.website", "instance", "Website", readonly=True
    )
    order_states = fields.One2Many(
        "magento.order_state", "instance", "Order States"
    )

    @classmethod
    @ModelView.button
    def import_order_states(cls, instances):
        """
        Import order states for instances

        :param instances: List of active records of instances
        """
        OrderState = Pool().get('magento.order_state')

        for instance in instances:

            Transaction().context.update({
                'magento_instance': instance.id
            })

            # Import order states
            with OrderConfig(
                instance.url, instance.api_user, instance.api_key
            ) as order_config_api:
                OrderState.create_all_using_magento_data(
                    order_config_api.get_states()
                )

    @staticmethod
    def default_active():
        """
        Sets default for active
        """
        return True

    @staticmethod
    def default_company():
        """
        Sets current company as default
        """
        return Transaction().context.get('company')

    @classmethod
    def __setup__(cls):
        """
        Setup the class before adding to pool
        """
        super(Instance, cls).__setup__()
        cls._sql_constraints += [
            (
                'unique_url', 'UNIQUE(url)',
                'URL of an instance must be unique'
            )
        ]
        cls._error_messages.update({
            "connection_error": "Incorrect API Settings! \n"
                "Please check and correct the API settings on instance.",
            "multiple_instances": 'Selected operation can be done only for one'
                ' instance at a time',
        })
        cls._buttons.update({
            'test_connection': {},
            'import_websites': {},
            'import_order_states': {}
        })

    @classmethod
    @ModelView.button_action('magento.wizard_test_connection')
    def test_connection(cls, instances):
        """
        Test magento connection and display appropriate message to user

        :param instances: Active record list of magento instance
        """
        if len(instances) != 1:
            cls.raise_user_error('multiple_instances')

        instance = instances[0]
        try:
            with magento.API(
                instance.url, instance.api_user, instance.api_key
            ):
                return
        except (
            xmlrpclib.Fault, IOError, xmlrpclib.ProtocolError, socket.timeout
        ):
            cls.raise_user_error("connection_error")

    @classmethod
    @ModelView.button_action('magento.wizard_import_websites')
    def import_websites(cls, instances):
        """
        Import the websites and their stores/view from magento

        :param instances: Active record list of magento instance
        """
        Website = Pool().get('magento.instance.website')
        Store = Pool().get('magento.website.store')
        StoreView = Pool().get('magento.store.store_view')
        MagentoOrderState = Pool().get('magento.order_state')

        if len(instances) != 1:
            cls.raise_user_error('multiple_instances')

        instance = instances[0]

        with Transaction().set_context(magento_instance=instance.id):

            # Import order states
            with OrderConfig(
                instance.url, instance.api_user, instance.api_key
            ) as order_config_api:
                MagentoOrderState.create_all_using_magento_data(
                    order_config_api.get_states()
                )

            # Import websites
            with Core(
                instance.url, instance.api_user, instance.api_key
            ) as core_api:
                websites = []
                stores = []

                mag_websites = core_api.websites()

                # Create websites
                for mag_website in mag_websites:
                    websites.append(Website.find_or_create(
                        instance, mag_website
                    ))

                for website in websites:
                    mag_stores = core_api.stores(
                        {'website_id': {'=': website.magento_id}}
                    )

                    # Create stores
                    for mag_store in mag_stores:
                        stores.append(Store.find_or_create(website, mag_store))

                for store in stores:
                    mag_store_views = core_api.store_views(
                        {'group_id': {'=': store.magento_id}}
                    )

                    # Create store views
                    for mag_store_view in mag_store_views:
                        StoreView.find_or_create(store, mag_store_view)


class InstanceWebsite(ModelSQL, ModelView):
    """
    Magento Instance Website

    A magento instance can have multiple websites.
    They act as  parents of stores. A website consists of one or more stores
    """
    __name__ = 'magento.instance.website'

    name = fields.Char('Name', required=True)
    code = fields.Char('Code', required=True, readonly=True)
    magento_id = fields.Integer('Magento ID', readonly=True, required=True)
    instance = fields.Many2One(
        'magento.instance', 'Instance', required=True, readonly=True,
    )
    company = fields.Function(
        fields.Many2One('company.company', 'Company'),
        'get_company'
    )
    stores = fields.One2Many(
        'magento.website.store', 'website', 'Stores',
        readonly=True,
    )
    default_uom = fields.Many2One('product.uom', 'Default Product UOM')
    magento_root_category_id = fields.Integer(
        'Magento Root Category ID', required=True
    )
    magento_product_templates = fields.One2Many(
        'magento.website.template', 'website', 'Magento Product Templates',
        readonly=True
    )

    def get_company(self, name):
        """
        Returns company related to instance

        :param name: Field name
        """
        return self.instance.company.id

    @staticmethod
    def default_magento_root_category_id():
        """
        Sets default root category id. Is set to 1, because the default
        root category is 1
        """
        return 1

    @staticmethod
    def default_default_uom():
        """
        Sets default product uom for website
        """
        ProductUom = Pool().get('product.uom')

        return ProductUom.search([('name', '=', 'Unit')])[0].id

    @classmethod
    def __setup__(cls):
        """
        Setup the class before adding to pool
        """
        super(InstanceWebsite, cls).__setup__()
        cls._sql_constraints += [
            (
                'magento_id_instance_unique', 'UNIQUE(magento_id, instance)',
                'A website must be unique in an instance'
            )
        ]

    @classmethod
    def find_or_create(cls, instance, values):
        """
        Looks for the website whose `values` are sent by magento against
        the instance with `instance` in tryton.
        If a record exists for this, return that else create a new one and
        return

        :param instance: Active record of instance
        :param values: Dictionary of values for a website sent by magento
        :return: Active record of record created/found
        """
        websites = cls.search([
            ('instance', '=', instance.id),
            ('magento_id', '=', int(values['website_id']))
        ])

        if websites:
            return websites[0]

        return cls.create([{
            'name': values['name'],
            'code': values['code'],
            'instance': instance.id,
            'magento_id': int(values['website_id']),
        }])[0]

    def export_inventory(self, websites):
        """
        Exports inventory stock information to magento

        :param websites: List of active records of website
        """
        for website in websites:
            website.export_inventory_to_magento()

    def export_inventory_to_magento(self):
        """
        Exports stock data of products from openerp to magento for this
        website

        :return: List of product templates
        """
        Location = Pool().get('stock.location')

        product_templates = []
        instance = self.instance

        locations = Location.search([('type', '=', 'storage')])

        for magento_product_template in self.magento_product_templates:
            product_template = magento_product_template.template
            product_templates.append(product_template)

            with Transaction().set_context({'locations': map(int, locations)}):
                product_data = {
                    'qty': product_template.quantity,
                    'is_in_stock': '1' if product_template.quantity > 0
                        else '0',
                }

                # Update stock information to magento
                with magento.Inventory(
                    instance.url, instance.api_user, instance.api_key
                ) as inventory_api:
                    inventory_api.update(
                        magento_product_template.magento_id, product_data
                    )

        return product_templates


class WebsiteStore(ModelSQL, ModelView):
    """
    Magento Website Store or Store view groups

    Stores are children of websites. The visibility of products and
    categories is managed on magento at store level by specifying the
    root category on a store.
    """
    __name__ = 'magento.website.store'

    name = fields.Char('Name', required=True)
    magento_id = fields.Integer('Magento ID', readonly=True, required=True)
    website = fields.Many2One(
        'magento.instance.website', 'Website', required=True,
        readonly=True,
    )
    instance = fields.Function(
        fields.Many2One('magento.instance', 'Instance'),
        'get_instance'
    )
    company = fields.Function(
        fields.Many2One('company.company', 'Company'),
        'get_company'
    )
    store_views = fields.One2Many(
        'magento.store.store_view', 'store', 'Store Views', readonly=True
    )

    def get_company(self, name):
        """
        Returns company related to website

        :param name: Field name
        """
        return self.website.company.id

    def get_instance(self, name):
        """
        Returns instance related to website

        :param name: Field name
        """
        return self.website.instance.id

    @classmethod
    def __setup__(cls):
        """
        Setup the class before adding to pool
        """
        super(WebsiteStore, cls).__setup__()
        cls._sql_constraints += [
            (
                'magento_id_website_unique', 'UNIQUE(magento_id, website)',
                'A store must be unique in a website'
            )
        ]

    @classmethod
    def find_or_create(cls, website, values):
        """
        Looks for the store whose `values` are sent by magento against the
        website with `website` in tryton.
        If a record exists for this, return that else create a new one and
        return

        :param website: Active record of website
        :param values: Dictionary of values for a store sent by magento
        :return: Active record of record created/found
        """
        stores = cls.search([
            ('website', '=', website.id),
            ('magento_id', '=', int(values['group_id']))
        ])

        if stores:
            return stores[0]

        return cls.create([{
            'name': values['name'],
            'magento_id': int(values['group_id']),
            'website': website.id,
        }])[0]


class WebsiteStoreView(ModelSQL, ModelView):
    """
    Magento Website Store View

    A store needs one or more store views to be browse-able in the front-end.
    It allows for multiple presentations of a store. Most implementations
    use store views for different languages
    """
    __name__ = 'magento.store.store_view'

    name = fields.Char('Name', required=True)
    code = fields.Char('Code', required=True, readonly=True)
    magento_id = fields.Integer('Magento ID', readonly=True, required=True)
    store = fields.Many2One(
        'magento.website.store', 'Store', required=True, readonly=True,
    )
    instance = fields.Function(
        fields.Many2One('magento.instance', 'Instance'),
        'get_instance'
    )
    website = fields.Function(
        fields.Many2One('magento.instance.website', 'Website'),
        'get_website'
    )
    company = fields.Function(
        fields.Many2One('company.company', 'Company'),
        'get_company'
    )

    def get_instance(self, name):
        """
        Returns instance related to store

        :param name: Field name
        """
        return self.store.instance.id

    def get_website(self, name):
        """
        Returns website related to store

        :param name: Field name
        """
        return self.store.website.id

    def get_company(self, name):
        """
        Returns company related to store

        :param name: Field name
        """
        return self.store.company.id

    @classmethod
    def __setup__(cls):
        """
        Setup the class before adding to pool
        """
        super(WebsiteStoreView, cls).__setup__()
        cls._sql_constraints += [
            (
                'magento_id_store_unique', 'UNIQUE(magento_id, store)',
                'A store view must be unique in a store'
            )
        ]

    @classmethod
    def find_or_create(cls, store, values):
        """
        Looks for the store view whose `values` are sent by magento against
        the store with `store` in tryton.
        If a record exists for this, return that else create a new one and
        return

        :param store: Active record of store
        :param values: Dictionary of values for store view sent by magento
        :return: Actice record of record created/found
        """
        store_views = cls.search([
            ('store', '=', store.id),
            ('magento_id', '=', int(values['store_id']))
        ])

        if store_views:
            return store_views[0]

        return cls.create([{
            'name': values['name'],
            'code': values['code'],
            'store': store.id,
            'magento_id': int(values['store_id']),
        }])[0]


class TestConnectionStart(ModelView):
    "Test Connection"
    __name__ = 'magento.wizard_test_connection.start'


class TestConnection(Wizard):
    """
    Test Connection Wizard

    Test the connection to magento instance(s)
    """
    __name__ = 'magento.wizard_test_connection'

    start = StateView(
        'magento.wizard_test_connection.start',
        'magento.wizard_test_connection_view_form',
        [
            Button('Ok', 'end', 'tryton-ok'),
        ]
    )

    def default_start(self, data):
        """Test the connection and show the user appropriate message

        :param data: Wizard data
        """
        return {}


class ImportWebsitesStart(ModelView):
    "Import Websites Start View"
    __name__ = 'magento.wizard_import_websites.start'


class ImportWebsites(Wizard):
    """
    Import Websites Wizard

    Import the websites and their stores/view from magento
    """
    __name__ = 'magento.wizard_import_websites'

    start = StateView(
        'magento.wizard_import_websites.start',
        'magento.wizard_import_websites_view_form',
        [
            Button('Ok', 'end', 'tryton-ok'),
        ]
    )

    def default_start(self, data):
        """Import the websites, store and store views and show user a
        confirmation message

        :param data: Wizard data
        """
        return {}


class ExportInventoryStart(ModelView):
    "Export Inventory Start View"
    __name__ = 'magento.wizard_export_inventory.start'


class ExportInventory(Wizard):
    """
    Export Inventory Wizard

    Export product stock information to magento for the current website
    """
    __name__ = 'magento.wizard_export_inventory'

    start = StateView(
        'magento.wizard_export_inventory.start',
        'magento.wizard_export_inventory_view_start_form',
        [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Continue', 'export_', 'tryton-ok', default=True),
        ]
    )

    export_ = StateAction('product.act_template_form')

    def do_export_(self, action):
        """Handles the transition"""

        Website = Pool().get('magento.instance.website')

        website = Website(Transaction().context.get('active_id'))

        product_templates = website.export_inventory_to_magento()

        action['pyson_domain'] = PYSONEncoder().encode(
            [('id', 'in', map(int, product_templates))])
        return action, {}

    def transition_export_(self):
        return 'end'
