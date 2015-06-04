# -*- coding: utf-8 -*-
"""
    wizard

    :copyright: (c) 2015 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
import magento
import json
from .api import Core

from trytond.model import ModelView, fields
from trytond.pool import PoolMeta, Pool
from trytond.transaction import Transaction
from trytond.pyson import PYSONEncoder
from trytond.wizard import (
    Wizard, StateView, Button, StateAction, StateTransition
)

__all__ = [
    'ExportMagentoInventoryStart', 'ExportMagentoInventory',
    'ExportMagentoShipmentStatusStart',
    'ExportMagentoShipmentStatus', 'ImportMagentoOrderStatesStart',
    'ImportMagentoOrderStates', 'ImportMagentoCarriersStart',
    'ImportMagentoCarriers', 'ConfigureMagento',
    'TestMagentoConnectionStart', 'ImportWebsitesStart',
    'ImportStoresStart', 'FailureStart', 'SuccessStart',
    'ExportMagentoOrderStatusStart', 'ExportMagentoOrderStatus',
    'UpdateMagentoCatalogStart', 'UpdateMagentoCatalog',
    'ExportMagentoCatalogStart', 'ExportMagentoCatalog'
]
__metaclass__ = PoolMeta


class ExportMagentoOrderStatusStart(ModelView):
    "Export Order Status Start View"
    __name__ = 'magento.wizard_export_order_status.start'

    message = fields.Text("Message", readonly=True)


class ExportMagentoOrderStatus(Wizard):
    """
    Export Order Status wizard

    Export order status to magento for the current store view
    """
    __name__ = 'magento.wizard_export_order_status'

    start = StateView(
        'magento.wizard_export_order_status.start',
        'magento.wizard_export_magento_order_status_view_start_form',
        [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Continue', 'export_', 'tryton-ok', default=True),
        ]
    )

    export_ = StateAction('magento.act_sale_form_all')

    def default_start(self, data):
        """
        Sets default data for wizard

        :param data: Wizard data
        """
        Channel = Pool().get('sale.channel')

        channel = Channel(Transaction().context.get('active_id'))
        channel.validate_magento_channel()
        return {
            'message':
                "This wizard will export orders status to magento " +
                "for this store view. All the orders edited/updated after " +
                "the Last Order Export Time will be exported."
        }

    def do_export_(self, action):
        """
        Export order status to magento
        """
        Channel = Pool().get('sale.channel')

        channel = Channel(Transaction().context.get('active_id'))
        channel.validate_magento_channel()

        sales = channel.export_order_status_to_magento()

        data = {'res_id': [sale.id for sale in sales]}
        return action, data

    def transition_export_(self):
        return 'end'


class ImportMagentoOrderStatesStart(ModelView):
    "Import Order States Start"
    __name__ = 'magento.wizard_import_order_states.start'


class ImportMagentoOrderStates(Wizard):
    """
    Wizard to import order states for channel
    """
    __name__ = 'magento.wizard_import_order_states'

    start = StateView(
        'magento.wizard_import_order_states.start',
        'magento.wizard_import_magento_order_states_start_view_form',
        [
            Button('Ok', 'end', 'tryton-ok'),
        ]
    )


class ImportMagentoCarriersStart(ModelView):
    "Import Carriers Start"
    __name__ = 'magento.wizard_import_carriers.start'

    message = fields.Text("Message", readonly=True)


class ImportMagentoCarriers(Wizard):
    """
    Wizard to import carriers / shipping methods for channel
    """
    __name__ = 'magento.wizard_import_carriers'

    start = StateView(
        'magento.wizard_import_carriers.start',
        'magento.wizard_import_magento_carriers_start_view_form',
        [
            Button('Ok', 'end', 'tryton-ok'),
        ]
    )

    def default_start(self, data):
        """
        Import carriers and show the user appropriate message

        :param data: Wizard data
        """
        Channel = Pool().get('sale.channel')

        channel = Channel(Transaction().context.get('active_id'))
        channel.validate_magento_channel()
        return {
            'message':
                "This wizard has imported all the carriers / " +
                "shipping methods for this magento channel. You should now " +
                "configure the imported carriers / shipping methods to " +
                "match the shipment carriers in Tryton to allow seamless " +
                "synchronisation of tracking information."
        }


class ExportMagentoInventoryStart(ModelView):
    "Export Inventory Start View"
    __name__ = 'magento.wizard_export_inventory.start'


class ExportMagentoInventory(Wizard):
    """
    Export Inventory Wizard

    Export product stock information to magento for the current website
    """
    __name__ = 'magento.wizard_export_inventory'

    start = StateView(
        'magento.wizard_export_inventory.start',
        'magento.wizard_export_magento_inventory_view_start_form',
        [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Continue', 'export_', 'tryton-ok', default=True),
        ]
    )

    export_ = StateAction('product.act_template_form')

    def do_export_(self, action):
        """
        Handles the transition
        """

        Channel = Pool().get('sale.channel')

        channel = Channel.get_current_magento_channel()

        product_templates = channel.export_inventory_to_magento()

        action['pyson_domain'] = PYSONEncoder().encode(
            [('id', 'in', map(int, product_templates))])
        return action, {}

    def transition_export_(self):
        return 'end'


class ExportMagentoShipmentStatusStart(ModelView):
    "Export Shipment Status View"
    __name__ = 'magento.wizard_export_shipment_status.start'

    message = fields.Text("Message", readonly=True)


class ExportMagentoShipmentStatus(Wizard):
    """
    Export Shipment Status Wizard

    Exports shipment status for sale orders related to current store view
    """
    __name__ = 'magento.wizard_export_shipment_status'

    start = StateView(
        'magento.wizard_export_shipment_status.start',
        'magento.wizard_export_magento_shipment_status_view_start_form',
        [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Continue', 'export_', 'tryton-ok', default=True),
        ]
    )

    export_ = StateAction('sale.act_sale_form')

    def default_start(self, data):
        """
        Sets default data for wizard

        :param data: Wizard data
        """
        Channel = Pool().get('sale.channel')

        channel = Channel(Transaction().context.get('active_id'))
        channel.validate_magento_channel()
        return {
            'message':
                "This wizard will export shipment status for all the " +
                "shipments related to this store view. To export tracking " +
                "information also for these shipments please check the " +
                "checkbox for Export Tracking Information on Store View."
        }

    def do_export_(self, action):
        """Handles the transition"""

        Channel = Pool().get('sale.channel')

        channel = Channel(Transaction().context.get('active_id'))
        channel.validate_magento_channel()

        sales = channel.export_shipment_status_to_magento()

        action['pyson_domain'] = PYSONEncoder().encode(
            [('id', 'in', map(int, sales))]
        )
        return action, {}

    def transition_export_(self):
        return 'end'


class ConfigureMagento(Wizard):
    """
    Wizard To Configure Magento
    """
    __name__ = 'magento.wizard_configure_magento'

    start = StateView(
        'magento.wizard_test_connection.start',
        'magento.wizard_test_magento_connection_view_form',
        [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Next', 'website', 'tryton-go-next', 'True'),
        ]
    )

    website = StateTransition()

    import_website = StateView(
        'magento.wizard_import_websites.start',
        'magento.wizard_import_websites_view_form',
        [
            Button('Next', 'store', 'tryton-go-next', 'True'),
        ]
    )

    store = StateTransition()

    import_store = StateView(
        'magento.wizard_import_stores.start',
        'magento.wizard_import_stores_view_form',
        [
            Button('Next', 'success', 'tryton-go-next', 'True'),
        ]
    )

    success = StateView(
        'magento.wizard_configuration_success.start',
        'magento.wizard_configuration_success_view_form',
        [
            Button('Ok', 'end', 'tryton-ok')
        ]
    )

    failure = StateView(
        'magento.wizard_configuration_failure.start',
        'magento.wizard_configuration_failure_view_form',
        [
            Button('Ok', 'end', 'tryton-ok')
        ]
    )

    def default_start(self, data):
        """
        Test the connection for current magento channel
        """
        Channel = Pool().get('sale.channel')

        magento_channel = Channel(Transaction().context.get('active_id'))
        magento_channel.validate_magento_channel()

        # Test Connection
        magento_channel.test_magento_connection()

        return {
            'channel': magento_channel.id
        }

    def transition_website(self):
        """
        Import websites for current magento channel
        """
        magento_channel = self.start.channel

        self.import_website.__class__.magento_websites.selection = \
            self.get_websites()

        if not (
            magento_channel.magento_website_id and
            magento_channel.magento_store_id
        ):
            return 'import_website'
        if not self.validate_websites():
            return 'failure'
        return 'end'

    def transition_store(self):
        """
        Initialize the values of website in sale channel
        """
        self.import_store.__class__.magento_stores.selection = \
            self.get_stores()

        return 'import_store'

    def default_success(self, data):
        """
        Initialize the values of store in sale channel
        """
        channel = self.start.channel
        imported_store = self.import_store.magento_stores
        imported_website = self.import_website.magento_websites

        magento_website = json.loads(imported_website)
        channel.magento_website_id = magento_website['id']
        channel.magento_website_name = magento_website['name']
        channel.magento_website_code = magento_website['code']

        magento_store = json.loads(imported_store)
        channel.magento_store_id = magento_store['store_id']
        channel.magento_store_name = magento_store['name']

        channel.save()
        return {}

    def get_websites(self):
        """
        Returns the list of websites
        """
        magento_channel = self.start.channel

        with Core(
            magento_channel.magento_url, magento_channel.magento_api_user,
            magento_channel.magento_api_key
        ) as core_api:
            websites = core_api.websites()

        selection = []

        for website in websites:
            # XXX: An UGLY way to map json to selection, fix me
            website_data = {
                'code': website['code'],
                'id': website['website_id'],
                'name': website['name']
            }
            website_data = json.dumps(website_data)
            selection.append((website_data, website['name']))

        return selection

    def get_stores(self):
        """
        Return list of all stores
        """
        magento_channel = self.start.channel

        selected_website = json.loads(self.import_website.magento_websites)

        with Core(
            magento_channel.magento_url, magento_channel.magento_api_user,
            magento_channel.magento_api_key
        ) as core_api:
            stores = core_api.stores(selected_website['id'])

        all_stores = []
        for store in stores:
            # Create the new dictionary of required values from a dictionary,
            # and convert it into the string
            store_data = {
                'store_id': store['default_store_id'],
                'name': store['name']
            }
            store_data = json.dumps(store_data)
            all_stores.append((store_data, store['name']))

        return all_stores

    def validate_websites(self):
        """
        Validate the website of magento channel
        """
        magento_channel = self.start.channel

        current_website_configurations = {
            'code': magento_channel.magento_website_code,
            'id': str(magento_channel.magento_website_id),
            'name': magento_channel.magento_website_name
        }

        current_website = (
            json.dumps(current_website_configurations),
            magento_channel.magento_website_name
        )
        if current_website not in self.get_websites():
            return False
        return True


class TestMagentoConnectionStart(ModelView):
    "Test Connection"
    __name__ = 'magento.wizard_test_connection.start'

    channel = fields.Many2One(
        'sale.channel', 'Sale Channel', required=True, readonly=True
    )


class ImportWebsitesStart(ModelView):
    """
    Import Websites Start View
    """
    __name__ = 'magento.wizard_import_websites.start'

    magento_websites = fields.Selection([], 'Select Website', required=True)


class ImportStoresStart(ModelView):
    """
    Import stores from websites
    """
    __name__ = 'magento.wizard_import_stores.start'

    magento_stores = fields.Selection([], 'Select Store', required=True)


class FailureStart(ModelView):
    """
    Failure wizard
    """
    __name__ = 'magento.wizard_configuration_failure.start'


class SuccessStart(ModelView):
    """
    Get Done
    """
    __name__ = 'magento.wizard_configuration_success.start'


class UpdateMagentoCatalogStart(ModelView):
    'Update Catalog View'
    __name__ = 'magento.update_catalog.start'


class UpdateMagentoCatalog(Wizard):
    '''
    Update Catalog

    This is a wizard to update already imported products
    '''
    __name__ = 'magento.update_catalog'

    start = StateView(
        'magento.update_catalog.start',
        'magento.magento_update_catalog_start_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Continue', 'update_', 'tryton-ok', default=True),
        ]
    )
    update_ = StateAction('product.act_template_form')

    def do_update_(self, action):
        """Handles the transition"""

        Channel = Pool().get('sale.channel')

        channel = Channel(Transaction().context.get('active_id'))
        channel.validate_magento_channel()

        product_template_ids = self.update_products(channel)

        action['pyson_domain'] = PYSONEncoder().encode(
            [('id', 'in', product_template_ids)])
        return action, {}

    def transition_import_(self):
        return 'end'

    def update_products(self, channel):
        """
        Updates products for current magento_channel

        :param channel: Browse record of channel
        :return: List of product IDs
        """
        products = []
        with Transaction().set_context({'current_channel': channel.id}):
            for listing in channel.product_listings:
                products.append(
                    listing.product.update_from_magento()
                )

        return map(int, products)


class ExportMagentoCatalogStart(ModelView):
    'Export Catalog View'
    __name__ = 'magento.export_catalog.start'

    category = fields.Many2One(
        'product.category', 'Magento Category', required=True,
        domain=[('magento_ids', 'not in', [])],
    )
    products = fields.Many2Many(
        'product.product', None, None, 'Products', required=True,
        domain=[('channel_listings', '=', None)],
    )
    attribute_set = fields.Selection(
        [], 'Attribute Set', required=True,
    )

    @classmethod
    def get_attribute_sets(cls):
        """Get the list of attribute sets from magento for the current channel

        :return: Tuple of attribute sets where each tuple consists of (ID,Name)
        """
        Channel = Pool().get('sale.channel')

        if not Transaction().context.get('active_id'):
            return []

        channel = Channel(Transaction().context['active_id'])
        channel.validate_magento_channel()

        with magento.ProductAttributeSet(
            channel.magento_url, channel.magento_api_user,
            channel.magento_api_key
        ) as attribute_set_api:
            attribute_sets = attribute_set_api.list()

        return [(
            attribute_set['set_id'], attribute_set['name']
        ) for attribute_set in attribute_sets]

    @classmethod
    def fields_view_get(cls, view_id=None, view_type='form'):
        """This method is overridden to populate the selection field for
        attribute_set with the attribute sets from the current channel's
        counterpart on magento.
        This overridding has to be done because `active_id` is not available
        if the meth:get_attribute_sets is called directly from the field.
        """
        rv = super(
            ExportMagentoCatalogStart, cls
        ).fields_view_get(view_id, view_type)
        rv['fields']['attribute_set']['selection'] = cls.get_attribute_sets()
        return rv


class ExportMagentoCatalog(Wizard):
    '''Export catalog

    Export the products selected to the selected category for this channel
    '''
    __name__ = 'magento.export_catalog'

    start = StateView(
        'magento.export_catalog.start',
        'magento.magento_export_catalog_start_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Continue', 'export_', 'tryton-ok', default=True),
        ]
    )
    export_ = StateAction('product.act_template_form')

    def do_export_(self, action):
        """
        Export the products selected to the selected category for this website
        """
        Channel = Pool().get('sale.channel')

        channel = Channel(Transaction().context['active_id'])
        channel.validate_magento_channel()

        with Transaction().set_context({
            'current_channel': channel.id,
            'magento_attribute_set': self.start.attribute_set,
        }):
            for product in self.start.products:
                product.export_to_magento(self.start.category)

        action['pyson_domain'] = PYSONEncoder().encode(
            [('id', 'in', map(int, self.start.products))])

        return action, {}

    def transition_export_(self):
        return 'end'
