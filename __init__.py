# -*- coding: utf-8 -*-
"""
    __init__

    Initialize Module

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
from trytond.pool import Pool
from magento_ import (
    Instance, InstanceWebsite, WebsiteStore, WebsiteStoreView
)


def register():
    """
    Register classes
    """
    Pool.register(
        Instance,
        InstanceWebsite,
        WebsiteStore,
        WebsiteStoreView,
        module='magento', type_='model'
    )
