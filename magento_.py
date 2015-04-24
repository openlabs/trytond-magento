# -*- coding: utf-8 -*-
"""
    magento_

    Magento

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
import json
from .api import Core

from trytond.model import ModelView, ModelSQL, fields
from trytond.pool import PoolMeta, Pool
from trytond.transaction import Transaction
from trytond.pyson import PYSONEncoder
from trytond.wizard import (
    Wizard, StateView, Button, StateAction, StateTransition
)

__all__ = [
    'ExportInventoryStart', 'ExportInventory',
    'ExportTierPricesStart', 'ExportTierPrices', 'MagentoTier',
    'ExportTierPricesStatus', 'ExportShipmentStatusStart',
    'ExportShipmentStatus', 'ImportOrderStatesStart', 'MagentoException',
    'ImportOrderStates', 'ImportCarriersStart', 'ImportCarriers',
    'ConfigureMagento', 'TestMagentoConnectionStart', 'ImportWebsitesStart',
    'ImportStoresStart', 'FailureStart', 'SuccessStart'
]
__metaclass__ = PoolMeta


class MagentoTier(ModelSQL, ModelView):
    """Price Tiers for store

    This model stores the default price tiers to be used while sending
    tier prices for a product from Tryton to Magento.
    The product also has a similar table like this. If there are no entries in
    the table on product, then these tiers are used.
    """
    __name__ = 'sale.channel.magento.price_tier'

    channel = fields.Many2One(
        'sale.channel', 'Magento Store', required=True, readonly=True,
    )
    quantity = fields.Float('Quantity', required=True)

    @classmethod
    def __setup__(cls):
        """
        Setup the class before adding to pool
        """
        super(MagentoTier, cls).__setup__()
        cls._sql_constraints += [
            (
                'channel_quantity_unique', 'UNIQUE(channel, quantity)',
                'Quantity in price tiers must be unique for a channel'
            )
        ]


class ImportOrderStatesStart(ModelView):
    "Import Order States Start"
    __name__ = 'magento.wizard_import_order_states.start'


class ImportOrderStates(Wizard):
    """
    Wizard to import order states for channel
    """
    __name__ = 'magento.wizard_import_order_states'

    start = StateView(
        'magento.wizard_import_order_states.start',
        'magento.wizard_import_order_states_start_view_form',
        [
            Button('Ok', 'end', 'tryton-ok'),
        ]
    )

    def default_start(self, data):
        """
        Import order states and show the user appropriate message

        :param data: Wizard data
        """
        return {}


class ImportCarriersStart(ModelView):
    "Import Carriers Start"
    __name__ = 'magento.wizard_import_carriers.start'

    message = fields.Text("Message", readonly=True)


class ImportCarriers(Wizard):
    """
    Wizard to import carriers / shipping methods for channel
    """
    __name__ = 'magento.wizard_import_carriers'

    start = StateView(
        'magento.wizard_import_carriers.start',
        'magento.wizard_import_carriers_start_view_form',
        [
            Button('Ok', 'end', 'tryton-ok'),
        ]
    )

    def default_start(self, data):
        """
        Import carriers and show the user appropriate message

        :param data: Wizard data
        """
        return {
            'message': "This wizard has imported all the carriers / " +
                "shipping methods for this magento channel. You should now " +
                "configure the imported carriers / shipping methods to " +
                "match the shipment carriers in Tryton to allow seamless " +
                "synchronisation of tracking information."
        }


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

        Channel = Pool().get('sale.channel')

        channel = Channel(Transaction().context.get('current_channel'))

        product_templates = channel.export_inventory_to_magento()

        action['pyson_domain'] = PYSONEncoder().encode(
            [('id', 'in', map(int, product_templates))])
        return action, {}

    def transition_export_(self):
        return 'end'


class ExportTierPricesStart(ModelView):
    "Export Tier Prices Start View"
    __name__ = 'magento.wizard_export_tier_prices.start'


class ExportTierPricesStatus(ModelView):
    "Export Tier Prices Status View"
    __name__ = 'magento.wizard_export_tier_prices.status'

    products_count = fields.Integer('Products Count', readonly=True)


class ExportTierPrices(Wizard):
    """
    Export Tier Prices Wizard

    Export product tier prices to magento for the current store
    """
    __name__ = 'magento.wizard_export_tier_prices'

    start = StateView(
        'magento.wizard_export_tier_prices.start',
        'magento.wizard_export_tier_prices_view_start_form',
        [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Continue', 'export_', 'tryton-ok', default=True),
        ]
    )

    export_ = StateView(
        'magento.wizard_export_tier_prices.status',
        'magento.wizard_export_tier_prices_view_status_form',
        [
            Button('OK', 'end', 'tryton-cancel'),
        ]
    )

    def default_export_(self, fields):
        """Export price tiers and return count of products"""
        Store = Pool().get('magento.website.store')

        store = Store(Transaction().context.get('active_id'))

        return {
            'products_count': store.export_tier_prices_to_magento()
        }


class ExportShipmentStatusStart(ModelView):
    "Export Shipment Status View"
    __name__ = 'magento.wizard_export_shipment_status.start'

    message = fields.Text("Message", readonly=True)


class ExportShipmentStatus(Wizard):
    """
    Export Shipment Status Wizard

    Exports shipment status for sale orders related to current store view
    """
    __name__ = 'magento.wizard_export_shipment_status'

    start = StateView(
        'magento.wizard_export_shipment_status.start',
        'magento.wizard_export_shipment_status_view_start_form',
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
        return {
            'message': "This wizard will export shipment status for all the " +
                "shipments related to this store view. To export tracking " +
                "information also for these shipments please check the " +
                "checkbox for Export Tracking Information on Store View."
        }

    def do_export_(self, action):
        """Handles the transition"""

        Channel = Pool().get('sale.channel')

        channel = Channel(Transaction().context.get('active_id'))

        sales = channel.export_shipment_status_to_magento()

        action['pyson_domain'] = PYSONEncoder().encode(
            [('id', 'in', map(int, sales))]
        )
        return action, {}

    def transition_export_(self):
        return 'end'


class MagentoException(ModelSQL, ModelView):
    """
    Magento Exception model
    """
    __name__ = 'magento.exception'

    origin = fields.Reference(
        "Origin", selection='models_get', select=True,
    )
    log = fields.Text('Exception Log')

    @classmethod
    def models_get(cls):
        '''
        Return valid models allowed for origin
        '''
        return [
            ('sale.sale', 'Sale'),
            ('sale.line', 'Sale Line'),
        ]


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
