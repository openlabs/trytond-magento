# -*- coding: utf-8 -*-
"""
    __init__

    Initialize Module

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
#Flake8: noqa
from trytond.pool import Pool
from .magento_ import *


def register():
    """
    Register classes
    """
    Pool.register(
        Instance,
        module='magento', type_='model'
    )
