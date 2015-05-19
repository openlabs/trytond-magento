# -*- coding: utf-8 -*-
"""
    sale

    Sale

    :copyright: (c) 2013-2015 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
import magento
from decimal import Decimal
import xmlrpclib

from trytond.model import ModelView, ModelSQL, fields
from trytond.transaction import Transaction
from trytond.exceptions import UserError
from trytond.pool import PoolMeta, Pool
from trytond.pyson import Eval, Not, Bool


__all__ = [
    'MagentoOrderState', 'StockShipmentOut', 'Sale', 'SaleLine',
]
__metaclass__ = PoolMeta

INVISIBLE_IF_NOT_MAGENTO = {
    'invisible': ~(Eval('channel_type') == 'magento'),
}


class MagentoOrderState(ModelSQL, ModelView):
    """
    Magento - Tryton Order State map

    This model stores a map of order states between tryton and Magento.
    This allows the user to configure the states mapping according to his/her
    convenience. This map is used to process orders in tryton when they are
    imported. This is also used to map the order status on magento when
    sales are exported. This also allows the user to determine in which state
    he/she wants the order to be imported in.
    """
    __name__ = 'magento.order_state'

    name = fields.Char('Name', required=True, readonly=True)
    code = fields.Char('Code', required=True, readonly=True)
    tryton_state = fields.Selection([
        ('sale.quotation', 'Sale - Quotation'),
        ('sale.processing', 'Sale - Processing'),
        ('sale.confirmed', 'Sale - Confirmed'),
        ('sale.done', 'Sale - Done'),
        ('sale.cancel', 'Sale - Canceled'),
        ('invoice.waiting', 'Invoice - Waiting'),
        ('invoice.paid', 'Invoice - Paid'),
    ], 'Tryton State', states={
        'invisible': Not(Bool(Eval('use_for_import'))),
        'required': Bool(Eval('use_for_import'))
    })
    use_for_import = fields.Boolean('Import orders in this magento state')
    invoice_method = fields.Selection([
        ('manual', 'Manual'),
        ('order', 'On Order Processed'),
        ('shipment', 'On Shipment Sent'),
    ], 'Invoice Method')
    shipment_method = fields.Selection([
        ('manual', 'Manual'),
        ('order', 'On Order Processed'),
        ('invoice', 'On Invoice Paid'),
    ], 'Shipment Method')
    channel = fields.Many2One(
        'sale.channel', 'Sale Channel', required=True,
        ondelete="CASCADE"
    )

    @staticmethod
    def default_use_for_import():
        """
        Sets default for use for import
        """
        return True

    @classmethod
    def __setup__(cls):
        """
        Setup the class before adding to pool
        """
        super(MagentoOrderState, cls).__setup__()
        cls._sql_constraints += [
            (
                'code_channel_unique', 'unique(code, channel)',
                'Each magento state must be unique by code in an channel'
            ),
        ]

    @classmethod
    def get_tryton_state(cls, name):
        """
        Returns tryton order state for magento state

        :param name: Name of the magento state
        :return: A dictionary of tryton state and shipment and invoice methods
        """
        if name in ('new', 'holded'):
            return {
                'tryton_state': 'sale.quotation',
                'invoice_method': 'order',
                'shipment_method': 'order'
            }
        elif name in ('pending_payment', 'payment_review'):
            return {
                'tryton_state': 'invoice.waiting',
                'invoice_method': 'order',
                'shipment_method': 'invoice'
            }

        elif name in ('closed', 'complete'):
            return {
                'tryton_state': 'sale.done',
                'invoice_method': 'order',
                'shipment_method': 'order'
            }

        elif name == 'processing':
            return {
                'tryton_state': 'sale.processing',
                'invoice_method': 'order',
                'shipment_method': 'order'
            }
        else:
            return {
                'tryton_state': 'sale.cancel',
                'invoice_method': 'manual',
                'shipment_method': 'manual'
            }

    @classmethod
    def create_all_using_magento_data(cls, magento_data):
        """This method expects a dictionary in which the key is the state
        code on magento and value is the state name on magento.
        This method will create each of the item in the dict as a record in
        this model.

        :param magento_data: Magento data in form of dict
        :return: List of active records of records created
        """
        Channel = Pool().get('sale.channel')

        order_states_to_create = []

        channel = Channel(Transaction().context['current_channel'])
        channel.validate_magento_channel()

        for code, name in magento_data.iteritems():
            if cls.search([
                ('code', '=', code),
                ('channel', '=', channel.id)
            ]):
                continue

            data_map = cls.get_tryton_state(code)
            data_map.update({
                'name': name,
                'code': code,
                'channel': channel.id,
            })
            order_states_to_create.append(data_map)

        return cls.create(order_states_to_create)


class Sale:
    "Sale"
    __name__ = 'sale.sale'

    magento_id = fields.Integer(
        'Magento ID', readonly=True, states=INVISIBLE_IF_NOT_MAGENTO,
        depends=['channel_type']
    )

    @classmethod
    def __setup__(cls):
        """
        Setup the class before adding to pool
        """
        super(Sale, cls).__setup__()
        cls._sql_constraints += [
            (
                'magento_id_channel_unique',
                'UNIQUE(magento_id, channel)',
                'A sale must be unique in an channel',
            )
        ]
        cls._error_messages.update({
            'invalid_channel': 'Store view must have same channel as sale '
                'order',
            'magento_exception': 'Magento exception in sale %s.'
        })

    @classmethod
    def confirm(cls, sales):
        "Validate sale before confirming"
        for sale in sales:
            if sale.has_channel_exception:
                cls.raise_user_error('magento_exception', sale.reference)
        super(Sale, cls).confirm(sales)

    @classmethod
    def find_or_create_using_magento_data(cls, order_data):
        """
        Find or Create sale using magento data

        :param order_data: Order Data from magento
        :return: Active record of record created/found
        """
        sale = cls.find_using_magento_data(order_data)

        if not sale:
            sale = cls.create_using_magento_data(order_data)

        return sale

    @classmethod
    def find_using_magento_data(cls, order_data):
        """
        Finds sale using magento data and returns that sale if found, else None

        :param order_data: Order Data from magento
        :return: Active record of record found
        """
        # Each sale has to be unique in an channel of magento
        sales = cls.search([
            ('magento_id', '=', int(order_data['order_id'])),
            ('channel', '=',
                Transaction().context.get('current_channel')),
        ])

        return sales and sales[0] or None

    @classmethod
    def get_sale_using_magento_data(cls, order_data):
        """
        Return an active record of the sale from magento data
        """
        Sale = Pool().get('sale.sale')
        Party = Pool().get('party.party')
        Address = Pool().get('party.address')
        Currency = Pool().get('currency.currency')
        Uom = Pool().get('product.uom')
        MagentoOrderState = Pool().get('magento.order_state')
        Channel = Pool().get('sale.channel')

        channel = Channel(Transaction().context['current_channel'])
        channel.validate_magento_channel()

        currency = Currency.search_using_magento_code(
            order_data['order_currency_code']
        )

        if order_data['customer_id']:
            party = Party.find_or_create_using_magento_id(
                order_data['customer_id']
            )
        else:
            party = Party.create_using_magento_data({
                'firstname': order_data['customer_firstname'],
                'lastname': order_data['customer_lastname'],
                'email': order_data['customer_email'],
                'customer_id': 0
            })

        party_invoice_address = None
        if order_data['billing_address']:
            party_invoice_address = \
                Address.find_or_create_for_party_using_magento_data(
                    party, order_data['billing_address']
                )

        party_shipping_address = None
        if order_data['shipping_address']:
            party_shipping_address = \
                Address.find_or_create_for_party_using_magento_data(
                    party, order_data['shipping_address']
                )
        unit, = Uom.search([('name', '=', 'Unit')])

        tryton_state = MagentoOrderState.get_tryton_state(order_data['state'])

        if not party_shipping_address:
            # if there is no shipment address, this could be a digital
            # delivery which won't need a shipment. No shipment_address is
            # hence assumed as no shipment needed. So set the method as
            # manual
            shipment_method = 'manual'
        else:
            shipment_method = tryton_state['shipment_method']

        return Sale(**{
            'reference': channel.magento_order_prefix +
                order_data['increment_id'],
            'sale_date': order_data['created_at'].split()[0],
            'party': party.id,
            'currency': currency.id,
            'invoice_address': party_invoice_address,
            'shipment_address': party_shipping_address or party_invoice_address,
            'magento_id': int(order_data['order_id']),
            'channel': channel.id,
            'invoice_method': tryton_state['invoice_method'],
            'shipment_method': shipment_method,
            'lines': [],
        })

    @classmethod
    def create_using_magento_data(cls, order_data):
        """
        Create a sale from magento data. If you wish to override the creation
        process, it is recommended to subclass and manipulate the returned
        unsaved active record from the `get_sale_using_magento_data` method.

        :param order_data: Order data from magento
        :return: Active record of record created
        """
        ChannelException = Pool().get('channel.exception')
        MagentoOrderState = Pool().get('magento.order_state')

        sale = cls.get_sale_using_magento_data(order_data)
        sale.save()

        sale.lines = list(sale.lines)
        sale.add_lines_using_magento_data(order_data)
        sale.save()

        # Process sale now
        tryton_state = MagentoOrderState.get_tryton_state(order_data['state'])
        try:
            sale.process_sale_using_magento_state(order_data['state'])
        except UserError, e:
            # Expecting UserError will only come when sale order has
            # channel exception.
            # Just ignore the error and leave this order in draft state
            # and let the user fix this manually.
            ChannelException.create([{
                'origin': '%s,%s' % (sale.__name__, sale.id),
                'log': "Error occurred on transitioning to state %s.\nError "
                    "Message: %s" % (tryton_state['tryton_state'], e.message),
                'channel': sale.channel.id,
            }])

        return sale

    def add_lines_using_magento_data(self, order_data):
        """
        Create sale lines from the magento data and associate them with
        the current sale.
        This method decides the actions to be taken on different product types

        :param order_data: Order Data from magento
        """
        Bom = Pool().get('production.bom')

        for item in order_data['items']:

            # If the product is a child product of a bundle product, do not
            # create a separate line for this.
            if 'bundle_option' in item['product_options'] and \
                    item['parent_item_id']:
                continue

            sale_line = self.get_sale_line_using_magento_data(item)
            if sale_line is not None:
                self.lines.append(sale_line)

        # Handle bundle products.
        # Find/Create BoMs for bundle products
        # If no bundle products exist in sale, nothing extra will happen
        Bom.find_or_create_bom_for_magento_bundle(order_data)

        if order_data.get('shipping_method'):
            self.lines.append(
                self.get_shipping_line_data_using_magento_data(order_data)
            )

        if Decimal(order_data.get('discount_amount')):
            self.lines.append(
                self.get_discount_line_data_using_magento_data(order_data)
            )

    def get_sale_line_using_magento_data(self, item):
        """
        Get sale.line data from magento data.
        """
        SaleLine = Pool().get('sale.line')
        Product = Pool().get('product.product')
        ChannelException = Pool().get('channel.exception')
        Channel = Pool().get('sale.channel')
        Uom = Pool().get('product.uom')

        sale_line = None
        unit, = Uom.search([('name', '=', 'Unit')])
        if not item['parent_item_id']:
            # If its a top level product, create it
            try:
                product = Product.find_or_create_using_magento_sku(item['sku'])
            except xmlrpclib.Fault, exception:
                if exception.faultCode == 101:
                    # Case when product doesnot exist on magento
                    # create magento exception
                    ChannelException.create([{
                        'origin': '%s,%s' % (self.__name__, self.id),
                        'log': "Product #%s does not exist" %
                            item['product_id'],
                        'channel': self.channel.id
                    }])
                    product = None
                else:
                    raise
            sale_line = SaleLine(**{
                'sale': self.id,
                'magento_id': int(item['item_id']),
                'description': item['name'] or product.name,
                'unit_price': Decimal(item['price']),
                'unit': unit.id,
                'quantity': Decimal(item['qty_ordered']),
                'note': item.get('comments'),
                'product': product,
            })
            if item.get('tax_percent') and Decimal(item.get('tax_percent')):
                channel = Channel.get_current_magento_channel()
                taxes = channel.get_taxes(
                    Decimal(item['tax_percent']) / 100
                )
                sale_line.taxes = taxes
        return sale_line

    @classmethod
    def find_or_create_using_magento_increment_id(cls, order_increment_id):
        """
        This method tries to find the sale with the order increment ID
        first and if not found it will fetch the info from magento and
        create a new sale with the data from magento using
        create_using_magento_data

        :param order_increment_id: Order increment ID from magento
        :type order_increment_id: string
        :returns: Active record of sale order created/found
        """
        Channel = Pool().get('sale.channel')

        channel = Channel(Transaction().context['current_channel'])
        channel.validate_magento_channel()

        sale = cls.find_using_magento_increment_id(order_increment_id)

        if not sale:
            with magento.Order(
                channel.magento_url, channel.magento_api_user,
                channel.magento_api_key
            ) as order_api:
                order_data = order_api.info(order_increment_id)

            sale = cls.create_using_magento_data(order_data)

        return sale

    @classmethod
    def find_using_magento_id(cls, order_id):
        """
        This method tries to find the sale with the magento ID and returns that
        sale if found else None

        :param order_id: Order ID from magento
        :type order_id: integer
        :returns: Active record of sale order created
        """
        # each sale has to be unique in an channel of magento
        sales = cls.search([
            ('magento_id', '=', order_id),
            ('channel', '=',
                Transaction().context.get('current_channel'))
        ])
        return sales and sales[0] or None

    @classmethod
    def find_using_magento_increment_id(cls, order_increment_id):
        """
        This method tries to find the sale with the order increment ID and
        returns that sale if found else None

        :param order_increment_id: Order Increment ID from magento
        :type order_increment_id: string
        :returns: Active record of sale order created
        """
        Channel = Pool().get('sale.channel')

        channel = Channel(Transaction().context.get('current_channel'))

        sales = cls.search([
            (
                'reference', '=', channel.magento_order_prefix +
                order_increment_id
            ),
            ('channel', '=', channel.id)
        ])

        return sales and sales[0] or None

    def get_shipping_line_data_using_magento_data(self, order_data):
        """
        Returns an unsaved shipping line active record for the given sale
        using magento data.

        :param order_data: Order Data from magento
        """
        Uom = Pool().get('product.uom')
        MagentoCarrier = Pool().get('magento.instance.carrier')
        SaleLine = Pool().get('sale.line')

        carrier_data = {}
        unit, = Uom.search([('name', '=', 'Unit')])

        # Fetch carrier code from shipping_method
        # ex: shipping_method : flaterate_flaterate
        #     carrier_code    : flaterate
        carrier_data['code'], _ = order_data['shipping_method'].split('_', 1)

        magento_carrier = MagentoCarrier.find_using_magento_data(carrier_data)

        if magento_carrier and magento_carrier.carrier:
            product = magento_carrier.carrier.carrier_product
        else:
            product = None

        return SaleLine(**{
            'sale': self.id,
            'description': order_data['shipping_description'] or
                    'Magento Shipping',
            'product': product,
            'unit_price': Decimal(order_data.get('shipping_amount', 0.00)),
            'unit': unit.id,
            'note': ' - '.join([
                    'Magento Shipping',
                    order_data['shipping_method'],
                    order_data['shipping_description']
            ]),
            'quantity': 1,
        })

    def get_discount_line_data_using_magento_data(self, order_data):
        """
        Returns an unsaved discount line AR for the given sale using magento
        data.

        :param order_data: Order Data from magento
        """
        SaleLine = Pool().get('sale.line')
        Uom = Pool().get('product.uom')

        unit, = Uom.search([('name', '=', 'Unit')])

        return SaleLine(**{
            'sale': self.id,
            'description': order_data['discount_description'] or
                'Magento Discount',
            'unit_price': Decimal(order_data.get('discount_amount', 0.00)),
            'unit': unit.id,
            'note': order_data['discount_description'],
            'quantity': 1,
        })

    def process_sale_using_magento_state(self, magento_state):
        """
        Process the sale in tryton based on the state of order
        when its imported from magento

        :param magento_state: State on magento the order was imported in
        """
        Sale = Pool().get('sale.sale')

        data = MagentoOrderState.get_tryton_state(magento_state)

        # If order is canceled, just cancel it
        if data['tryton_state'] == 'sale.cancel':
            Sale.cancel([self])
            return

        # Order is not canceled, move it to quotation
        Sale.quote([self])
        Sale.confirm([self])

        if data['tryton_state'] not in ['sale.quotation', 'sale.confirmed']:
            Sale.process([self])

    def export_order_status_to_magento(self):
        """
        Export order status to magento.

        :return: Active record of sale
        """
        if not self.magento_id:
            return self

        channel = self.channel

        channel.validate_magento_channel()

        increment_id = self.reference.split(channel.magento_order_prefix)[1]
        # This try except is placed because magento might not accept this
        # order status change due to its workflow constraints.
        # TODO: Find a better way to do it
        try:
            with magento.Order(
                channel.magento_url, channel.magento_api_user,
                channel.magento_api_key
            ) as order_api:
                if self.state == 'cancel':
                    order_api.cancel(increment_id)
                elif self.state == 'done':
                    # TODO: update shipping and invoice
                    order_api.addcomment(increment_id, 'complete')
        except xmlrpclib.Fault, exception:
            if exception.faultCode == 103:
                return self

        return self


class SaleLine:
    "Sale Line"
    __name__ = 'sale.line'

    #: This field stores the magento ID corresponding to this sale line
    magento_id = fields.Integer('Magento ID', readonly=True)


class StockShipmentOut:
    """Stock Shipment Out

    Add a field for tracking number
    """
    __name__ = 'stock.shipment.out'

    tracking_number = fields.Char('Tracking Number')
    carrier = fields.Many2One('carrier', 'Carrier')

    #: Indicates if the tracking information has been exported
    #: to magento. Tracking info means carrier and tracking number info
    #: which is different from exporting shipment status to magento
    is_tracking_exported_to_magento = fields.Boolean(
        'Is Tracking Info Exported To Magento'
    )
    #: The magento increment id for this shipment. This is filled when a
    #: shipment is created corresponding to the shipment to tryton
    #: in magento.
    magento_increment_id = fields.Char(
        "Magento Increment ID", readonly=True
    )

    @staticmethod
    def default_is_tracking_exported_to_magento():
        return False

    def export_tracking_info_to_magento(self):
        """
        Export tracking info to magento for the specified shipment.

        :param shipment: Browse record of shipment
        :return: Shipment increment ID
        """
        MagentoCarrier = Pool().get('magento.instance.carrier')
        Channel = Pool().get('sale.channel')
        Shipment = Pool().get('stock.shipment.out')

        channel = Channel(Transaction().context['current_channel'])
        channel.validate_magento_channel()

        carriers = MagentoCarrier.search([
            ('channel', '=', channel.id),
            ('carrier', '=', self.carrier.id)
        ])

        if not carriers:
            # The carrier linked to this shipment is not found mapped to a
            # magento carrier.
            return

        # Add tracking info to the shipment on magento
        with magento.Shipment(
            channel.magento_url, channel.magento_api_user,
            channel.magento_api_key
        ) as shipment_api:
            shipment_increment_id = shipment_api.addtrack(
                self.magento_increment_id,
                carriers[0].code,
                carriers[0].title,
                self.tracking_number,
            )

            Shipment.write([self], {
                'is_tracking_exported_to_magento': True
            })

        return shipment_increment_id
