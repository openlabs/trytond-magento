# -*- coding: utf-8 -*-
"""
    test_base

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
import os
import json
import unittest
from datetime import datetime

from dateutil.relativedelta import relativedelta
import trytond.tests.test_tryton
from trytond.tests.test_tryton import POOL, USER
from trytond.transaction import Transaction


ROOT_JSON_FOLDER = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'json'
)


def load_json(resource, filename):
    """Reads the json file from the filesystem and returns the json loaded as
    python objects

    On filesystem, the files are kept in this format:
        json----
              |
            resource----
                       |
                       filename

    :param resource: The magento resource for which the file has to be
                     fetched. It is same as the folder name in which the files
                     are kept.
    :param filename: The name of the file to be fethced without `.json`
                     extension.
    :returns: Loaded json from the contents of the file read.
    """
    file_path = os.path.join(
        ROOT_JSON_FOLDER, resource, str(filename)
    ) + '.json'

    return json.loads(open(file_path).read())


class TestBase(unittest.TestCase):
    """
    Setup basic defaults
    """

    def setUp(self):
        """
        Set up data used in the tests.
        this method is called before each test function execution.
        """
        trytond.tests.test_tryton.install_module('magento')

    def setup_defaults(self):
        """
        Setup default data
        """
        Instance = POOL.get('magento.instance')
        Website = POOL.get('magento.instance.website')
        Store = POOL.get('magento.website.store')
        StoreView = POOL.get('magento.store.store_view')
        Uom = POOL.get('product.uom')
        Currency = POOL.get('currency.currency')
        Company = POOL.get('company.company')
        Party = POOL.get('party.party')
        User = POOL.get('res.user')
        FiscalYear = POOL.get('account.fiscalyear')
        Sequence = POOL.get('ir.sequence')
        SequenceStrict = POOL.get('ir.sequence.strict')
        AccountTemplate = POOL.get('account.account.template')
        CreateChartAccount = POOL.get(
            'account.create_chart', type="wizard"
        )
        Account = POOL.get('account.account')
        PaymentTerm = POOL.get('account.invoice.payment_term')

        self.usd, = Currency.create([{
            'name': 'US Dollar',
            'code': 'USD',
            'symbol': '$',
        }])

        with Transaction().set_context(company=None):
            self.party, = Party.create([{
                'name': 'ABC',
            }])
            self.company, = Company.create([{
                'party': self.party.id,
                'currency': self.usd.id,
            }])

        User.write([User(USER)], {
            'main_company': self.company.id,
            'company': self.company.id,
        })

        # Create two instances
        self.instance1, = Instance.create([{
            'name': 'Test Instance 1',
            'url': 'some test url 1',
            'api_user': 'admin',
            'api_key': 'testkey',
            'company': self.company
        }])
        self.instance2, = Instance.create([{
            'name': 'Test Instance 2',
            'url': 'some test url 2',
            'api_user': 'admin',
            'api_key': 'testkey',
            'company': self.company
        }])

        # Search product uom
        self.uom, = Uom.search([
            ('name', '=', 'Unit'),
        ])

        # Create one website under each instance
        self.website1, = Website.create([{
            'name': 'A test website 1',
            'magento_id': 1,
            'code': 'test_code',
            'instance': self.instance1,
        }])
        self.website2, = Website.create([{
            'name': 'A test website 2',
            'magento_id': 1,
            'code': 'test_code',
            'instance': self.instance2,
        }])

        self.store, = Store.create([{
            'name': 'Store1',
            'magento_id': 1,
            'website': self.website1,
        }])

        self.store_view, = StoreView.create([{
            'name': 'Store view1',
            'magento_id': 1,
            'store': self.store,
            'code': '123',
        }])

        date = datetime.utcnow().date()

        with Transaction().set_context(
            User.get_preferences(context_only=True)
        ):
            invoice_sequence, = SequenceStrict.create([{
                'name': '%s' % date.year,
                'code': 'account.invoice',
                'company': self.company.id,
            }])
            fiscal_year, = FiscalYear.create([{
                'name': '%s' % date.year,
                'start_date': date + relativedelta(month=1, day=1),
                'end_date': date + relativedelta(month=12, day=31),
                'company': self.company.id,
                'post_move_sequence': Sequence.create([{
                    'name': '%s' % date.year,
                    'code': 'account.move',
                    'company': self.company.id,
                }])[0].id,
                'out_invoice_sequence': invoice_sequence.id,
                'in_invoice_sequence': invoice_sequence.id,
                'out_credit_note_sequence': invoice_sequence.id,
                'in_credit_note_sequence': invoice_sequence.id,
            }])
            FiscalYear.create_period([fiscal_year])

            account_template, = AccountTemplate.search(
                [('parent', '=', None)]
            )

            session_id, _, _ = CreateChartAccount.create()
            create_chart = CreateChartAccount(session_id)
            create_chart.account.account_template = account_template
            create_chart.account.company = self.company
            create_chart.transition_create_account()
            revenue, = Account.search([
                ('kind', '=', 'revenue'),
                ('company', '=', self.company.id),
            ])
            receivable, = Account.search([
                ('kind', '=', 'receivable'),
                ('company', '=', self.company.id),
            ])
            payable, = Account.search([
                ('kind', '=', 'payable'),
                ('company', '=', self.company.id),
            ])
            expense, = Account.search([
                ('kind', '=', 'expense'),
                ('company', '=', self.company.id),
            ])
            create_chart.properties.company = self.company
            create_chart.properties.account_receivable = receivable
            create_chart.properties.account_payable = payable
            create_chart.properties.account_revenue = revenue
            create_chart.properties.account_expense = expense
            create_chart.transition_create_properties()

            Party.write(
                [Party(self.party)], {
                    'account_payable': payable.id,
                    'account_receivable': receivable.id,
                }
            )
            PaymentTerm.create([{
                'name': 'Direct',
                'lines': [('create', [{'type': 'remainder'}])]
            }])

    def get_account_by_kind(self, kind, company=None, silent=True):
        """Returns an account with given spec

        :param kind: receivable/payable/expense/revenue
        :param silent: dont raise error if account is not found
        """
        Account = POOL.get('account.account')
        Company = POOL.get('company.company')

        if company is None:
            company, = Company.search([], limit=1)

        accounts = Account.search([
            ('kind', '=', kind),
            ('company', '=', company.id)
        ], limit=1)
        if not accounts and not silent:
            raise Exception("Account not found")
        return accounts[0] if accounts else False
