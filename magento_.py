# -*- coding: utf-8 -*-
"""
    magento_

    Magento

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
from trytond.model import ModelView, ModelSQL, fields
from trytond.transaction import Transaction


__all__ = ['Instance', 'InstanceWebsite', 'WebsiteStore', 'WebsiteStoreView']


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

    def get_company(self, name):
        """
        Returns company related to instance

        :param name: Field name
        """
        return self.instance.company.id

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
