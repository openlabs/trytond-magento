# -*- coding: utf-8 -*-
"""
    __init__

    Initialize Module

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
from trytond.pool import Pool
from magento_ import (
    TestConnectionStart, TestConnection, ImportWebsitesStart, ImportWebsites,
    ExportInventoryStart, ExportInventory, MagentoTier,
    ExportTierPricesStart, ExportTierPrices, ExportTierPricesStatus,
    ExportShipmentStatusStart, ExportShipmentStatus, ImportOrderStatesStart,
    ImportOrderStates, ImportCarriersStart, ImportCarriers, MagentoException
)
from channel import Channel
from party import Party, MagentoWebsiteParty, Address
from product import (
    Category, MagentoInstanceCategory, Product,
    ImportCatalogStart, ImportCatalog, UpdateCatalogStart, UpdateCatalog,
    ProductPriceTier, ExportCatalogStart, ExportCatalog,
    ProductSaleChannelListing
)
from country import Country, Subdivision
from currency import Currency
from carrier import MagentoInstanceCarrier
from sale import (
    MagentoOrderState, Sale, ImportOrdersStart, ImportOrders,
    ExportOrderStatusStart, ExportOrderStatus, StockShipmentOut, SaleLine
)
from bom import BOM
from tax import MagentoTax, MagentoTaxRelation


def register():
    """
    Register classes
    """
    Pool.register(
        Channel,
        MagentoTier,
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
        Product,
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
        MagentoTax,
        MagentoTaxRelation,
        ProductSaleChannelListing,
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
