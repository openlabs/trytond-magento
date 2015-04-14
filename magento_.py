# -*- coding: utf-8 -*-
"""
    magento_

    Magento

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
from trytond.model import ModelView, ModelSQL, fields
from trytond.pool import PoolMeta, Pool
from trytond.transaction import Transaction
from trytond.pyson import PYSONEncoder
from trytond.wizard import Wizard, StateView, Button, StateAction

__all__ = [
    'TestConnectionStart', 'TestConnection', 'ImportWebsitesStart',
    'ImportWebsites', 'ExportInventoryStart', 'ExportInventory',
    'ExportTierPricesStart', 'ExportTierPrices', 'MagentoTier',
    'ExportTierPricesStatus', 'ExportShipmentStatusStart',
    'ExportShipmentStatus', 'ImportOrderStatesStart', 'MagentoException',
    'ImportOrderStates', 'ImportCarriersStart', 'ImportCarriers'
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


class TestConnectionStart(ModelView):
    "Test Connection"
    __name__ = 'magento.wizard_test_connection.start'


class TestConnection(Wizard):
    """
    Test Connection Wizard

    Test the connection to magento channel(s)
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

    message = fields.Text("Message", readonly=True)


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
        """
        Import the websites, store and store views and show user a
        confirmation message

        :param data: Wizard data
        """
        return {
            'message': "This wizard has imported all the websites for this " +
                "magento channel. It has also imported all the stores and " +
                "store views related to the websites imported. If any of " +
                "the records existed already, it wont be imported."
        }


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
