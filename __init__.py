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
    ExportInventoryStart, ExportInventory, StorePriceTier,
    ExportTierPricesStart, ExportTierPrices, ExportTierPricesStatus,
    ExportShipmentStatusStart, ExportShipmentStatus, ImportOrderStatesStart,
    ImportOrderStates, ImportCarriersStart, ImportCarriers, MagentoException
)
from party import Party, MagentoWebsiteParty, Address
from product import (
    Category, MagentoInstanceCategory, Template, MagentoWebsiteTemplate,
    ImportCatalogStart, ImportCatalog, UpdateCatalogStart, UpdateCatalog,
    ProductPriceTier, ExportCatalogStart, ExportCatalog
)
from country import Country, Subdivision
from currency import Currency
from carrier import MagentoInstanceCarrier
from sale import (
    MagentoOrderState, Sale, ImportOrdersStart, ImportOrders,
    ExportOrderStatusStart, ExportOrderStatus, StockShipmentOut, SaleLine
)
from bom import BOM


def register():
    """
    Register classes
    """
    Pool.register(
        Instance,
        InstanceWebsite,
        WebsiteStore,
        StorePriceTier,
        WebsiteStoreView,
        MagentoInstanceCarrier,
        TestConnectionStart,
        ImportWebsitesStart,
        ExportInventoryStart,
        ExportTierPricesStart,
        ExportTierPricesStatus,
        ExportShipmentStatusStart,
        Country,
        Subdivision,
        Party,
        MagentoWebsiteParty,
        Category,
        MagentoException,
        MagentoInstanceCategory,
        Template,
        MagentoWebsiteTemplate,
        ProductPriceTier,
        ImportCatalogStart,
        ExportCatalogStart,
        MagentoOrderState,
        StockShipmentOut,
        Address,
        UpdateCatalogStart,
        Currency,
        Sale,
        ImportOrdersStart,
        ImportOrderStatesStart,
        ImportCarriersStart,
        ExportOrderStatusStart,
        SaleLine,
        BOM,
        module='magento', type_='model'
    )
    Pool.register(
        TestConnection,
        ImportWebsites,
        ImportOrderStates,
        ExportInventory,
        ExportTierPrices,
        ExportShipmentStatus,
        ImportCatalog,
        UpdateCatalog,
        ExportCatalog,
        ImportOrders,
        ExportOrderStatus,
        ImportCarriers,
        module='magento', type_='wizard'
    )
