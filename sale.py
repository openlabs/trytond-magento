# -*- coding: utf-8 -*-
"""
    sale

    Sale

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
from trytond.model import ModelView, ModelSQL, fields
from trytond.transaction import Transaction
from trytond.pyson import Eval, Not, Bool


__all__ = ['MagentoOrderState']


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
