# -*- coding: utf-8 -*-
import sys
if sys.version_info < (3, 8, 0):
    try:
        __version__ = __import__('pkg_resources').get_distribution('pygisceclient').version
    except Exception as e: # noqa
        __version__ = 'unknown'
else:
    try:
        import importlib.metadata
        __version__ = importlib.metadata.version('pygisceclient')
    except: # noqa
        __version__ = 'unknown'



from __future__ import absolute_import
from .restapi import RestApiClient
from .msgpack import MsgPackClient
