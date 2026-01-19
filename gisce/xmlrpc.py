from __future__ import absolute_import
import uuid
from .base import BaseClient, PositionArgumentsModel, to_dot
from .compat import ServerProxy, SafeTransport, httplib


class XmlRpcModel(PositionArgumentsModel):
    def _call(self, method, *args, **kwargs):
        payload = (
            self.api.database,
            self.api.uid,
            self.api.password,
            self._name,
            method
        ) + args
        return self.api.object.execute(*payload)


class XmlRpcClient(BaseClient):
    model_class = XmlRpcModel

    class BaseTransportWithRequestId(SafeTransport):
        def send_content(self, connection, request_body):
            connection.putheader("X-Request-Id", str(uuid.uuid4()))
            SafeTransport.send_content(self, connection, request_body)

    class UnverifiedSSLTransport(SafeTransport):
        def make_connection(self, host):
            import ssl
            context = ssl._create_unverified_context()
            self._connection = httplib.HTTPSConnection(host, context=context)
            return self._connection

        def send_content(self, connection, request_body):
            connection.putheader("X-Request-Id", str(uuid.uuid4()))
            SafeTransport.send_content(self, connection, request_body)

    def __init__(self, url, database, token=None, user=None, password=None, verify=None):
        super(XmlRpcClient, self).__init__()
        self.url = url + '/xmlrpc'
        if verify is not None and not verify:
            self.server_proxy_kwargs = {'transport': self.UnverifiedSSLTransport()}
        else:
            self.server_proxy_kwargs = {'transport': self.BaseTransportWithRequestId()}
        self.common = ServerProxy(self.url + '/common', allow_none=True, **self.server_proxy_kwargs)
        self.object = ServerProxy(self.url + '/object', allow_none=True, **self.server_proxy_kwargs)
        self.report_service = ServerProxy(self.url + '/report', allow_none=True, **self.server_proxy_kwargs)
        self.database = database
        self.uid = None
        self.password = None
        if token:
            self.uid = 'token'
            self.password = token
        else:
            self.login(user, password)
        self.models = self.object.obj_list(
            self.database, self.uid, self.password
        )

    def login(self, user, password):
        uid = self.common.login(self.database, user, password)
        if uid:
            self.uid = uid
            self.password = password
        else:
            raise ValueError('Error with user/password')

    def report(self, object, ids, datas=None, context=None):
        return self.report_service.report(
            self.database, self.uid, self.password, object, ids, datas, context
        )

    def report_get(self, report_id):
        return self.report_service.report_get(
            self.database, self.uid, self.password, report_id
        )
