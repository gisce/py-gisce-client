from __future__ import absolute_import
from .base import RequestsClient, PositionArgumentsModel
try:
    import msgpack
    MSGPACK_AVAILABLE = True
except ImportError:
    MSGPACK_AVAILABLE = False


class MsgPackProtocol(object):
    def __init__(self, api, endpoint):
        self.api = api
        self.endpoint = endpoint

    def __getattr__(self, item):
        def wrapper(*args, **kwargs):
            return self._call(item, *args, **kwargs)
        return wrapper

    def _call(self, method, *args, **kwargs):
        payload = list((
            method,
            self.api.database,
            self.api.uid,
            self.api.password,
        ) + args)
        if self.api.content_type == 'application/json':
            response = self.api.post(self.endpoint, json=payload)
            result = response.json()
        else:
            response = self.api.post(
                self.endpoint, data=msgpack.packb(payload),
                headers={'Content-Type': self.api.content_type}
            )
            result = msgpack.unpackb(response.content, raw=False)
        if response.status_code != 200:
            raise Exception(result['exception'])
        else:
            return result


class MsgPackModel(PositionArgumentsModel):
    def __init__(self, name, api):
        self.protocol = MsgPackProtocol(
            api, 'object'
        )
        super(MsgPackModel, self).__init__(name, api)

    def _call(self, method, *args, **kwargs):
        return self.protocol.execute(
            self._name,
            method,
            *args
        )


class MsgPackClient(RequestsClient):
    model_class = MsgPackModel

    def __init__(self, url, database, token=None, user=None, password=None,
                 content_type='json'):
        super(MsgPackClient, self).__init__(url, token, user, password)
        self.database = database
        assert content_type in ('json', 'msgpack')
        if content_type == 'msgpack' and not MSGPACK_AVAILABLE:
            raise Exception('msgpack is not available in this system')
        self.content_type = 'application/{}'.format(content_type)
        self.headers.pop('Authorization', None)
        self.auth = None
        self.uid = None
        self.password = None
        if token:
            self.uid = 'token'
            self.password = token
        else:
            self.login(user, password)
        self.report_service = MsgPackProtocol(self, 'report')

    def login(self, user, password):
        result = self.post('common', json=['login', self.database, user, password])
        if result.status_code == 200:
            self.uid = result.json()
            self.password = password
        else:
            raise ValueError('Error with user/password')

    def report(self, object, ids, datas=None, context=None):
        return self.report_service.report(object, ids, datas, context)

    def report_get(self, report_id):
        return self.report_service.report_get(report_id)
