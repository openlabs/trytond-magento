# -*- coding: utf-8 -*-
"""
    sale

    Sale

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
import magento
from decimal import Decimal

from trytond.model import ModelView, ModelSQL, fields
from trytond.transaction import Transaction
from trytond.pool import PoolMeta, Pool
from trytond.pyson import Eval, Not, Bool


__all__ = ['MagentoOrderState', 'Sale']
__metaclass__ = PoolMeta


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
    instance = fields.Many2One(
        'magento.instance', 'Magento Instance', required=True,
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
                'code_instance_unique', 'unique(code, instance)',
                'Each magento state must be unique by code in an instance'
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
        new_records = []

        for code, name in magento_data.iteritems():
            if cls.search([
                ('code', '=', code),
                ('instance', '=',
                    Transaction().context.get('magento_instance'))
            ]):
                continue

            vals = cls.get_tryton_state(code)
            vals.update({
                'name': name,
                'code': code,
                'instance': Transaction().context.get('magento_instance'),
            })
            new_records.extend(cls.create([vals]))

        return new_records


class Sale:
    "Sale"
    __name__ = 'sale.sale'

    magento_id = fields.Integer('Magento ID', readonly=True)
    magento_instance = fields.Many2One(
        'magento.instance', 'Magento Instance', readonly=True,
    )
    magento_store_view = fields.Many2One(
        'magento.store.store_view', 'Store View', readonly=True,
    )

    @classmethod
    def __setup__(cls):
        """
        Setup the class before adding to pool
        """
        super(Sale, cls).__setup__()
        cls._sql_constraints += [
            (
                'magento_id_instance_unique',
                'UNIQUE(magento_id, magento_instance)',
                'A sale must be unique in an instance',
            )
        ]
        cls._constraints += [
            ('check_store_view_instance', 'invalid_instance'),
        ]
        cls._error_messages.update({
            'invalid_instance': 'Store view must have same instance as sale '
                'order',
        })

    def check_store_view_instance(self):
        """
        Checks if instance of store view is same as instance of sale order
        """
        if self.magento_store_view.instance != self.magento_instance:
            return False
        return True

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
        # Each sale has to be unique in an instance of magento
        sales = cls.search([
            ('magento_id', '=', int(order_data['order_id'])),
            ('magento_instance', '=',
                Transaction().context.get('magento_instance')),
        ])

        return sales and sales[0] or None

    @classmethod
    def create_using_magento_data(cls, order_data):
        """
        Create a sale from magento data

        :param order_data: Order data from magento
        :return: Active record of record created
        """
        Party = Pool().get('party.party')
        Address = Pool().get('party.address')
        ProductTemplate = Pool().get('product.template')
        StoreView = Pool().get('magento.store.store_view')
        Currency = Pool().get('currency.currency')
        Uom = Pool().get('product.uom')

        store_view = StoreView(Transaction().context.get('magento_store_view'))
        instance = store_view.instance

        currency = Currency.search_using_magento_code(
            order_data['order_currency_code']
        )
        party = Party.find_or_create_using_magento_id(
            order_data['customer_id']
        )
        party_invoice_address = \
            Address.find_or_create_for_party_using_magento_data(
                party, order_data['billing_address']
            )
        party_shipping_address = \
            Address.find_or_create_for_party_using_magento_data(
                party, order_data['shipping_address']
            )
        unit, = Uom.search([('name', '=', 'Unit')])

        tryton_state = MagentoOrderState.get_tryton_state(order_data['state'])

        sale_data = {
            'reference': instance.order_prefix + order_data['increment_id'],
            'sale_date': order_data['created_at'].split()[0],
            'party': party.id,
            'currency': currency.id,
            'invoice_address': party_invoice_address.id,
            'shipment_address': party_shipping_address.id,
            'magento_id': int(order_data['order_id']),
            'magento_instance': instance.id,
            'magento_store_view': store_view.id,
            'invoice_method': tryton_state['invoice_method'],
            'shipment_method': tryton_state['shipment_method'],
            'lines': [
                ('create', [{
                    'description': item['name'],
                    'unit_price': Decimal(item['price']),
                    'unit': unit.id,
                    'quantity': Decimal(item['qty_ordered']),
                    'note': item['product_options'],
                    'product': ProductTemplate.find_or_create_using_magento_id(
                        item['product_id'],
                    ).products[0].id
                }]) for item in order_data['items']
            ]
        }

        if Decimal(order_data.get('shipping_amount')):
            sale_data['lines'].append(
                cls.get_shipping_line_data_using_magento_data(order_data)
            )

        if Decimal(order_data.get('discount_amount')):
            sale_data['lines'].append(
                cls.get_discount_line_data_using_magento_data(order_data)
            )

        sale, = cls.create([sale_data])

        # Process sale now
        sale.process_sale_using_magento_state(order_data['state'])

        return sale

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
        Instance = Pool().get('magento.instance')

        sale = cls.find_using_magento_increment_id(order_increment_id)

        if not sale:
            instance = Instance(Transaction().context.get('magento_instance'))

            with magento.Order(
                instance.url, instance.api_user, instance.api_key
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
        # each sale has to be unique in an instance of magento
        sales = cls.search([
            ('magento_id', '=', order_id),
            ('magento_instance', '=',
                Transaction().context.get('magento_instance'))
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
        Instance = Pool().get('magento.instance')

        instance = Instance(Transaction().context.get('magento_instance'))

        sales = cls.search([
            ('reference', '=', instance.order_prefix + order_increment_id),
            ('magento_instance', '=',
                Transaction().context.get('magento_instance'))
        ])

        return sales and sales[0] or None

    @classmethod
    def get_shipping_line_data_using_magento_data(cls, order_data):
        """
        Create a shipping line for the given sale using magento data

        :param order_data: Order Data from magento
        """
        Uom = Pool().get('product.uom')

        unit, = Uom.search([('name', '=', 'Unit')])

        return ('create', [{
            'description': 'Magento Shipping',
            'unit_price': Decimal(order_data.get('shipping_amount', 0.00)),
            'unit': unit.id,
            'note': ' - '.join([
                    order_data['shipping_method'],
                    order_data['shipping_description']
            ]),
            'quantity': 1,
        }])

    @classmethod
    def get_discount_line_data_using_magento_data(cls, order_data):
        """
        Create a discount line for the given sale using magento data

        :param order_data: Order Data from magento
        """
        Uom = Pool().get('product.uom')

        unit, = Uom.search([('name', '=', 'Unit')])

        return (
            'create', [{
                'description': order_data['discount_description']
                    or 'Magento Discount',
                'unit_price': Decimal(order_data.get('discount_amount', 0.00)),
                'unit': unit.id,
                'note': order_data['discount_description'],
                'quantity': 1,
            }]
        )

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
