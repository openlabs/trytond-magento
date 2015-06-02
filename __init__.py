# -*- coding: utf-8 -*-
"""
    __init__

    Initialize Module

    :copyright: (c) 2013-2015 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
from trytond.pool import Pool
from wizard import (
    TestMagentoConnectionStart, ImportWebsitesStart,
    ExportMagentoInventoryStart, ExportMagentoInventory,
    ExportMagentoShipmentStatusStart,
    ExportMagentoShipmentStatus, ImportMagentoOrderStatesStart,
    ImportMagentoOrderStates, ImportMagentoCarriersStart,
    ImportMagentoCarriers, ConfigureMagento, ImportStoresStart, FailureStart,
    SuccessStart, ExportMagentoOrderStatusStart, ExportMagentoOrderStatus,
    UpdateMagentoCatalogStart, UpdateMagentoCatalog,
    ExportMagentoCatalogStart, ExportMagentoCatalog,
)
from channel import Channel, MagentoTier
from party import Party, MagentoWebsiteParty, Address
from product import (
    Category, MagentoInstanceCategory, Product,
    ProductPriceTier, ProductSaleChannelListing
)
from country import Country, Subdivision
from currency import Currency
from carrier import MagentoInstanceCarrier
from sale import (
    MagentoOrderState, Sale, StockShipmentOut, SaleLine
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
        ExportMagentoInventoryStart,
        ExportMagentoShipmentStatusStart,
        Country,
        Subdivision,
        Party,
        MagentoWebsiteParty,
        Category,
        MagentoInstanceCategory,
        Product,
        ProductPriceTier,
        ExportMagentoCatalogStart,
        MagentoOrderState,
        StockShipmentOut,
        Address,
        UpdateMagentoCatalogStart,
        Currency,
        Sale,
        ImportMagentoOrderStatesStart,
        ImportMagentoCarriersStart,
        ExportMagentoOrderStatusStart,
        SaleLine,
        BOM,
        MagentoTax,
        MagentoTaxRelation,
        ProductSaleChannelListing,
        module='magento', type_='model'
    )
    Pool.register(
        ImportMagentoOrderStates,
        ExportMagentoInventory,
        ExportMagentoShipmentStatus,
        UpdateMagentoCatalog,
        ExportMagentoCatalog,
        ExportMagentoOrderStatus,
        ImportMagentoCarriers,
        ConfigureMagento,
        module='magento', type_='wizard'
    )
