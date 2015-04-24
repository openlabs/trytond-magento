# -*- coding: utf-8 -*-
"""
    __init__

    Initialize Module

    :copyright: (c) 2013-2015 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
from trytond.pool import Pool
from magento_ import (
    TestMagentoConnectionStart, ImportWebsitesStart,
    ExportInventoryStart, ExportInventory, MagentoTier,
    ExportTierPricesStart, ExportTierPrices, ExportTierPricesStatus,
    ExportShipmentStatusStart, ExportShipmentStatus, ImportOrderStatesStart,
    ImportOrderStates, ImportCarriersStart, ImportCarriers, MagentoException,
    ConfigureMagento, ImportStoresStart, FailureStart, SuccessStart
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
        TestMagentoConnectionStart,
        ImportStoresStart,
        FailureStart,
        SuccessStart,
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
        ConfigureMagento,
        module='magento', type_='wizard'
    )
