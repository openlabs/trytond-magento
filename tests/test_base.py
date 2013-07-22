# -*- coding: utf-8 -*-
"""
    test_base

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
import os
import json
import unittest

import trytond.tests.test_tryton
from trytond.tests.test_tryton import POOL


def load_json(resource, filename):
    """Reads the json file from the filesystem and returns the json loaded as
    python objects

    On filesystem, the files are kept in this format:
        json----
              |
            resource----
                       |
                       filename

    :param resource: The prestashop resource for which the file has to be
                     fetched. It is same as the folder name in which the files
                     are kept.
    :param filename: The name of the file to be fethced without `.json`
                     extension.
    :returns: Loaded json from the contents of the file read.
    """
    root_json_folder = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'json'
    )
    file_path = os.path.join(
        root_json_folder, resource, str(filename)
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

        self.party, = Party.create([{
            'name': 'ABC',
        }])
        self.usd, = Currency.create([{
            'name': 'US Dollar',
            'code': 'USD',
            'symbol': '$',
        }])
        self.company, = Company.create([{
            'party': self.party.id,
            'currency': self.usd.id,
        }])

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
