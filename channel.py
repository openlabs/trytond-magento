# -*- coding: utf-8 -*-
"""
    channel

    :copyright: (c) 2015 by Openlabs Technologies & Consulting (P) Limited
    :license: see LICENSE for more details.
"""
from datetime import datetime
import magento
import xmlrpclib
import socket

from trytond.pool import PoolMeta, Pool
from trytond.transaction import Transaction
from trytond.pyson import Eval
from trytond.model import ModelView, ModelSQL, fields
from .api import OrderConfig

__metaclass__ = PoolMeta
__all__ = ['Channel', 'MagentoTier', 'MagentoException']

MAGENTO_STATES = {
    'invisible': ~(Eval('source') == 'magento'),
    'required': Eval('source') == 'magento'
}

INVISIBLE_IF_NOT_MAGENTO = {
    'invisible': ~(Eval('source') == 'magento'),
}


class Channel:
    """
    Sale Channel model
    """
    __name__ = 'sale.channel'

    # Instance
    magento_url = fields.Char(
        "Magento Site URL", states=MAGENTO_STATES, depends=['source']
    )
    magento_api_user = fields.Char(
        "API User", states=MAGENTO_STATES, depends=['source']
    )
    magento_api_key = fields.Char(
        "API Key", states=MAGENTO_STATES, depends=['source']
    )
    magento_order_states = fields.One2Many(
        "magento.order_state", "channel", "Order States", readonly=True,
        states=INVISIBLE_IF_NOT_MAGENTO, depends=['source']
    )
    magento_carriers = fields.One2Many(
        "magento.instance.carrier", "channel", "Carriers / Shipping Methods",
        states=INVISIBLE_IF_NOT_MAGENTO, depends=['source']
    )
    magento_order_prefix = fields.Char(
        'Sale Order Prefix',
        help="This helps to distinguish between orders from different channels",
        states=INVISIBLE_IF_NOT_MAGENTO, depends=['source']
    )

    # website
    magento_website_id = fields.Integer(
        'Website ID', readonly=True,
        states=INVISIBLE_IF_NOT_MAGENTO, depends=['source']
    )
    magento_website_name = fields.Char(
        'Website Name', readonly=True,
        states=INVISIBLE_IF_NOT_MAGENTO, depends=['source']
    )
    magento_website_code = fields.Char(
        'Website Code', readonly=True,
        states=INVISIBLE_IF_NOT_MAGENTO, depends=['source']
    )
    magento_root_category_id = fields.Integer(
        'Root Category ID', states=INVISIBLE_IF_NOT_MAGENTO, depends=['source']
    )
    magento_store_name = fields.Char(
        'Store Name', readonly=True, states=INVISIBLE_IF_NOT_MAGENTO,
        depends=['source']
    )
    magento_store_id = fields.Integer(
        'Store ID', readonly=True, states=INVISIBLE_IF_NOT_MAGENTO,
        depends=['source']
    )
    magento_last_order_import_time = fields.DateTime(
        'Last Order Import Time', states=INVISIBLE_IF_NOT_MAGENTO,
        depends=['source']
    )
    magento_last_order_export_time = fields.DateTime(
        "Last Order Export Time", states=INVISIBLE_IF_NOT_MAGENTO,
        depends=['source']
    )

    #: Last time at which the shipment status was exported to magento
    magento_last_shipment_export_time = fields.DateTime(
        'Last shipment export time', states=INVISIBLE_IF_NOT_MAGENTO,
        depends=['source']
    )

    #: Checking this will make sure that only the done shipments which have a
    #: carrier and tracking reference are exported.
    magento_export_tracking_information = fields.Boolean(
        'Export tracking information', help='Checking this will make sure'
        ' that only the done shipments which have a carrier and tracking '
        'reference are exported. This will update carrier and tracking '
        'reference on magento for the exported shipments as well.',
        states=INVISIBLE_IF_NOT_MAGENTO, depends=['source']
    )
    magento_taxes = fields.One2Many(
        "sale.channel.magento.tax", "channel", "Taxes",
        states=INVISIBLE_IF_NOT_MAGENTO, depends=['source']
    )
    magento_price_tiers = fields.One2Many(
        'sale.channel.magento.price_tier', 'channel', 'Default Price Tiers',
        states=INVISIBLE_IF_NOT_MAGENTO, depends=['source']
    )
    product_listings = fields.One2Many(
        'product.product.channel_listing', 'channel', 'Product Listings',
    )

    @classmethod
    def __setup__(cls):
        """
        Setup the class before adding to pool
        """
        super(Channel, cls).__setup__()
        cls._sql_constraints += [
            (
                'unique_magento_channel',
                    'UNIQUE(magento_url, magento_website_id, magento_store_id)',
                'This store is already added'
            )
        ]
        cls._error_messages.update({
            "connection_error": "Incorrect API Settings! \n"
                "Please check and correct the API settings on channel.",
            "multiple_channels": 'Selected operation can be done only for one'
                ' channel at a time',
            'invalid_magento_channel':
                'Current channel does not belongs to Magento !'
        })
        cls._buttons.update({
            'import_magento_order_states': {},
            'import_magento_carriers': {},
            'configure_magento_connection': {}
        })
        cls._error_messages.update({
            "missing_magento_channel": 'Magento channel is not in context',
        })

    def validate_magento_channel(self):
        """
        Make sure channel source is magento
        """
        if self.source != 'magento':
            self.raise_user_error('invalid_magento_channel')

    @classmethod
    def get_source(cls):
        """
        Get the source
        """
        res = super(Channel, cls).get_source()
        res.append(('magento', 'Magento'))
        return res

    @staticmethod
    def default_magento_order_prefix():
        """
        Sets default value for magento order prefix
        """
        return 'mag_'

    @staticmethod
    def default_magento_root_category_id():
        """
        Sets default root category id. Is set to 1, because the default
        root category is 1
        """
        return 1

    def get_taxes(self, rate):
        "Return list of tax records with the given rate"
        for mag_tax in self.magento_taxes:
            if mag_tax.tax_percent == rate:
                return list(mag_tax.taxes)
        return []

    @classmethod
    @ModelView.button_action('magento.wizard_import_magento_order_states')
    def import_magento_order_states(cls, channels):
        """
        Import order states for magento channel

        :param channels: List of active records of channels
        """
        OrderState = Pool().get('magento.order_state')

        for channel in channels:
            channel.validate_magento_channel()
            with Transaction().set_context({'current_channel': channel.id}):
                # Import order states
                with OrderConfig(
                    channel.magento_url, channel.magento_api_user,
                    channel.magento_api_key
                ) as order_config_api:
                    OrderState.create_all_using_magento_data(
                        order_config_api.get_states()
                    )

    @classmethod
    @ModelView.button_action('magento.wizard_configure_magento')
    def configure_magento_connection(cls, channels):
        """
        Configure magento connection for current channel

        :param channels: List of active records of channels
        """
        pass

    def test_magento_connection(self):
        """
        Test magento connection and display appropriate message to user
        :param channels: Active record list of magento channels
        """
        # Make sure channel belongs to magento
        self.validate_magento_channel()

        try:
            with magento.API(
                self.magento_url, self.magento_api_user,
                self.magento_api_key
            ):
                return
        except (
            xmlrpclib.Fault, IOError, xmlrpclib.ProtocolError, socket.timeout
        ):
            self.raise_user_error("connection_error")

    @classmethod
    @ModelView.button_action('magento.wizard_import_magento_carriers')
    def import_magento_carriers(cls, channels):
        """
        Import carriers/shipping methods from magento for channels

        :param channels: Active record list of magento channels
        """
        InstanceCarrier = Pool().get('magento.instance.carrier')

        for channel in channels:
            channel.validate_magento_channel()
            with Transaction().set_context({'current_channel': channel.id}):
                with OrderConfig(
                    channel.magento_url, channel.magento_api_user,
                    channel.magento_api_key
                ) as order_config_api:
                    mag_carriers = order_config_api.get_shipping_methods()

                InstanceCarrier.create_all_using_magento_data(mag_carriers)

    @classmethod
    def get_current_magento_channel(cls):
        """Helper method to get the current magento_channel.
        """
        channel_id = Transaction().context.get('current_channel')
        if not channel_id:
            cls.raise_user_error('missing_magento_channel')
        return cls(channel_id)

    def import_magento_products(self):
        "Import products for this magento channel"
        Product = Pool().get('product.template')

        self.validate_magento_channel()

        with Transaction().set_context({'current_channel': self.id}):
            with magento.Product(
                self.magento_url, self.magento_api_user, self.magento_api_key
            ) as product_api:
                # TODO: Implement pagination and import each product as async
                # task
                magento_products = product_api.list()

                products = []
                for magento_product in magento_products:
                    products.append(
                        Product.find_or_create_using_magento_data(
                            magento_product
                        )
                    )

        return map(int, products)

    def import_order_from_magento(self):
        """
        Imports sale from magento

        :return: List of active record of sale imported
        """
        Sale = Pool().get('sale.sale')
        MagentoOrderState = Pool().get('magento.order_state')

        self.validate_magento_channel()

        new_sales = []
        with Transaction().set_context({'current_channel': self.id}):
            order_states = MagentoOrderState.search([
                ('channel', '=', self.id),
                ('use_for_import', '=', True)
            ])
            order_states_to_import_in = map(
                lambda state: state.code, order_states
            )

            if not order_states_to_import_in:
                self.raise_user_error("states_not_found")

            with magento.Order(
                self.magento_url, self.magento_api_user, self.magento_api_key
            ) as order_api:
                # Filter orders with date and store_id using list()
                # then get info of each order using info()
                # and call find_or_create_using_magento_data on sale
                filter = {
                    'store_id': {'=': self.magento_store_id},
                    'state': {'in': order_states_to_import_in},
                }
                if self.magento_last_order_import_time:
                    last_order_import_time = \
                        self.magento_last_order_import_time.replace(
                            microsecond=0
                        )
                    filter.update({
                        'updated_at': {
                            'gteq': last_order_import_time.isoformat(' ')
                        },
                    })
                self.write([self], {
                    'magento_last_order_import_time': datetime.utcnow()
                })
                orders = order_api.list(filter)
                for order in orders:
                    new_sales.append(
                        Sale.find_or_create_using_magento_data(
                            order_api.info(order['increment_id'])
                        )
                    )

        return new_sales

    @classmethod
    def export_order_status_to_magento_using_cron(cls):
        """
        Export sales orders status to magento using cron

        :param store_views: List of active record of store view
        """
        channels = cls.search([('source', '=', 'magento')])

        for channel in channels:
            channel.export_order_status_to_magento()

    def export_order_status_to_magento(self):
        """
        Export sale orders to magento for the current store view.
        If last export time is defined, export only those orders which are
        updated after last export time.

        :return: List of active records of sales exported
        """
        Sale = Pool().get('sale.sale')

        self.validate_magento_channel()

        exported_sales = []
        domain = [('channel', '=', self.id)]

        if self.magento_last_order_export_time:
            domain = [
                ('write_date', '>=', self.magento_last_order_export_time)
            ]

        sales = Sale.search(domain)

        self.magento_last_order_export_time = datetime.utcnow()
        self.save()

        for sale in sales:
            exported_sales.append(sale.export_order_status_to_magento())

        return exported_sales

    @classmethod
    def import_magento_orders(cls):
        """
        Import orders from magento for magento channels
        """
        channels = cls.search([('source', '=', 'magento')])

        for channel in channels:
            channel.import_order_from_magento()

    @classmethod
    def export_shipment_status_to_magento_using_cron(cls):
        """
        Export Shipment status for shipments using cron
        """
        channels = cls.search([('source', '=', 'magento')])

        for channel in channels:
            channel.export_shipment_status_to_magento()

    def export_shipment_status_to_magento(self):
        """
        Exports shipment status for shipments to magento, if they are shipped

        :return: List of active record of shipment
        """
        Shipment = Pool().get('stock.shipment.out')
        Sale = Pool().get('sale.sale')
        SaleLine = Pool().get('sale.line')

        self.validate_magento_channel()

        sale_domain = [
            ('channel', '=', self.id),
            ('shipment_state', '=', 'sent'),
            ('magento_id', '!=', None),
            ('shipments', '!=', None),
        ]

        if self.magento_last_shipment_export_time:
            sale_domain.append(
                ('write_date', '>=', self.magento_last_shipment_export_time)
            )

        sales = Sale.search(sale_domain)

        self.magento_last_shipment_export_time = datetime.utcnow()
        self.save()

        for sale in sales:
            # Get the increment id from the sale reference
            increment_id = sale.reference[
                len(self.magento_order_prefix): len(sale.reference)
            ]

            for shipment in sale.shipments:
                try:
                    # Some checks to make sure that only valid shipments are
                    # being exported
                    if shipment.is_tracking_exported_to_magento or \
                            shipment.state not in ('packed', 'done') or \
                            shipment.magento_increment_id:
                        sales.pop(sale)
                        continue
                    with magento.Shipment(
                        self.magento_url, self.magento_api_user,
                        self.magento_api_key
                    ) as shipment_api:
                        item_qty_map = {}
                        for move in shipment.outgoing_moves:
                            if isinstance(move.origin, SaleLine) \
                                    and move.origin.magento_id:
                                # This is done because there can be multiple
                                # lines with the same product and they need
                                # to be send as a sum of quanitities
                                item_qty_map.setdefault(
                                    str(move.origin.magento_id), 0
                                )
                                item_qty_map[str(move.origin.magento_id)] += \
                                    move.quantity
                        shipment_increment_id = shipment_api.create(
                            order_increment_id=increment_id,
                            items_qty=item_qty_map
                        )
                        Shipment.write(list(sale.shipments), {
                            'magento_increment_id': shipment_increment_id,
                        })

                        if self.magento_export_tracking_information and (
                            shipment.tracking_number and shipment.carrier
                        ):
                            shipment.export_tracking_info_to_magento()
                except xmlrpclib.Fault, fault:
                    if fault.faultCode == 102:
                        # A shipment already exists for this order,
                        # we cannot do anything about it.
                        # Maybe it was already exported earlier or was created
                        # separately on magento
                        # Hence, just continue
                        continue

        return sales

    @classmethod
    def export_inventory_to_magento_using_cron(cls):
        """
        Cron method to export inventory to magento
        """
        channels = cls.search([('source', '=', 'magento')])

        for channel in channels:
            channel.export_inventory_to_magento()

    def export_inventory_to_magento(self):
        """
        Exports stock data of products from tryton to magento for this
        channel
        :return: List of product templates
        """
        Location = Pool().get('stock.location')

        self.validate_magento_channel()

        products = []
        locations = Location.search([('type', '=', 'storage')])

        for listing in self.product_listings:
            product = listing.product
            products.append(product)

            with Transaction().set_context({'locations': map(int, locations)}):
                product_data = {
                    'qty': product.quantity,
                    'is_in_stock': '1' if listing.product.quantity > 0
                        else '0',
                }

                # Update stock information to magento
                with magento.Inventory(
                    self.magento_url, self.magento_api_user,
                    self.magento_api_key
                ) as inventory_api:
                    inventory_api.update(
                        listing.product_identifier, product_data
                    )

        return products

    @classmethod
    def export_tier_prices_to_magento_using_cron(cls):
        """
        Export tier prices to magento using cron
        """
        channels = cls.search([('source', '=', 'magento')])

        for channel in channels:
            channel.export_tier_prices_to_magento()

    def export_tier_prices_to_magento(self):
        """
        Exports tier prices of products from tryton to magento for this channel
        :return: List of products
        """
        self.validate_magento_channel()

        for listing in self.product_listings:

            # Get the price tiers from the product listing if the list has
            # price tiers else get the default price tiers from current
            # channel
            price_tiers = listing.price_tiers or self.magento_price_tiers

            price_data = []
            for tier in price_tiers:
                if hasattr(tier, 'product_listing'):
                    # The price tier comes from a product listing, then it has a
                    # function field for price, we use it directly
                    price = tier.price
                else:
                    # The price tier comes from the default tiers on
                    # channel,
                    # we dont have a product on tier, so we use the current
                    # product in loop for computing the price for this tier
                    price = self.price_list.compute(
                        None, listing.product, listing.product.list_price,
                        tier.quantity, self.default_uom
                    )

                price_data.append({
                    'qty': tier.quantity,
                    'price': float(price),
                })

            # Update stock information to magento
            with magento.ProductTierPrice(
                self.magento_url, self.magento_api_user, self.magento_api_key
            ) as tier_price_api:
                tier_price_api.update(
                    listing.product_identifier, price_data
                )

        return len(self.product_listings)


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
        domain=[('source', '=', 'magento')]
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
