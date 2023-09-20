# -*- coding: utf-8 -*-
from __future__ import absolute_import
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


from .restapi import RestApiClient
from .msgpack import MsgPackClient
from .xmlrpc import XmlRpcClient
from .xmlprc_wst import XmlRpcClientWst

PROTOCOL_MAP = {
    'restapi': RestApiClient,
    'msgpack': MsgPackClient,
    'xmlrpc': XmlRpcClient,
    'xmlrpc-wst': XmlRpcClientWst,
}


def connect(url, *args, **kwargs):
    import re
    for protocol, client in PROTOCOL_MAP.items():
        pattern = re.compile(r'http[s]?\+{}://*'.format(protocol))
        if pattern.match(url):
            url = re.sub(r'\+{}'.format(protocol), '', url)
            return client(url, *args, **kwargs)
