import sys
PY2 = sys.version_info < (3, 0, 0)

if PY2:
    from xmlrpclib import ServerProxy
else:
    from xmlrpc.client import ServerProxy
