import sys
from getpass import getpass
PY2 = sys.version_info < (3, 0, 0)

if PY2:
    from xmlrpclib import ServerProxy, SafeTransport
    import httplib
else:
    from xmlrpc.client import ServerProxy, SafeTransport
    import http.client as httplib


def is_interactive():
    """Detect if running in an interactive Python session (REPL, IPython, Jupyter, etc.)"""
    if hasattr(sys, 'ps1'):
        return True
    try:
        if sys.stdin.isatty():
            return True
    except AttributeError:
        pass
    try:
        import builtins
        get_ipython = getattr(builtins, 'get_ipython', None)
        if get_ipython is not None and get_ipython() is not None:
            return True
    except (AttributeError, RuntimeError):
        pass
    return False


def prompt_password(label='Password: '):
    return getpass(label)
