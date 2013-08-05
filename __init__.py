# -*- coding: utf-8 -*-
"""
    __init__

    Initialize Module

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
from trytond.pool import Pool
from magento_ import (
    Instance, InstanceWebsite, WebsiteStore, WebsiteStoreView,
    TestConnectionStart, TestConnection, ImportWebsitesStart, ImportWebsites,
)
from party import Party, MagentoWebsiteParty, Address
from product import (
    Category, MagentoInstanceCategory, Template, MagentoWebsiteTemplate,
    ImportCatalogStart, ImportCatalog, UpdateCatalogStart, UpdateCatalog
)
from country import Country, Subdivision
from sale import MagentoOrderState


def register():
    """
    Register classes
    """
    Pool.register(
        Instance,
        InstanceWebsite,
        WebsiteStore,
        WebsiteStoreView,
        TestConnectionStart,
        ImportWebsitesStart,
        Country,
        Subdivision,
        Party,
        MagentoWebsiteParty,
        Category,
        MagentoInstanceCategory,
        Template,
        MagentoWebsiteTemplate,
        ImportCatalogStart,
        MagentoOrderState,
        Address,
        UpdateCatalogStart,
        module='magento', type_='model'
    )
    Pool.register(
        TestConnection,
        ImportWebsites,
        ImportCatalog,
        UpdateCatalog,
        module='magento', type_='wizard'
    )
