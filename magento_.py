# -*- coding: utf-8 -*-
"""
    magento_

    Magento

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
from trytond.model import ModelView, ModelSQL


__all__ = ['Instance']


class Instance(ModelSQL, ModelView):
    "Instance"
    __name__ = 'magento.instance'
