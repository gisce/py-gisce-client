from __future__ import absolute_import
from .base import BaseClient, PositionArgumentsModel, to_dot
from .compat import ServerProxy


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

    def __init__(self, url, database, token=None, user=None, password=None):
        super(XmlRpcClient, self).__init__()
        self.url = url + '/xmlrpc'
        self.common = ServerProxy(self.url + '/common', allow_none=True)
        self.object = ServerProxy(self.url + '/object', allow_none=True)
        self.report_service = ServerProxy(self.url + '/report', allow_none=True)
        self.database = database
        self.uid = None
        self.password = None
        if token:
            self.uid = 'token'
            self.password = token
        else:
            self.login(user, password)

    def login(self, user, password):
        uid = self.common.login(self.database, user, password)
        if uid:
            self.uid = uid
            self.password = password
        else:
            raise ValueError('Error with user/password')

    def model(self, model):
        return self.model_class(model, self)

    def report(self, object, ids, datas=None, context=None):
        return self.report_service.report(
            self.database, self.uid, self.password, object, ids, datas, context
        )

    def report_get(self, report_id):
        return self.report_service.report_get(
            self.database, self.uid, self.password, report_id
        )

    def __getattr__(self, item):
        return self.model(to_dot(item))
