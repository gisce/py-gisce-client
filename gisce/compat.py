import sys
PY2 = sys.version_info < (3, 0, 0)

if PY2:
    from xmlrpclib import ServerProxy, SafeTransport
    import httplib
else:
    from xmlrpc.client import ServerProxy, SafeTransport
    import http.client as httplib
