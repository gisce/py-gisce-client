from __future__ import absolute_import
from .base import Client, Model
try:
    import msgpack
    MSGPACK_AVAILABLE = True
except ImportError:
    MSGPACK_AVAILABLE = False


class MsgPackModel(Model):
    def _call(self, method, *args, **kwargs):
        payload = list((
            'execute',
            self.api.database,
            self.api.uid,
            self.api.password,
            self._name,
            method
        ) + args)
        if self.api.content_type == 'application/json':
            return self.api.post('object', json=payload).json()
        else:
            result = self.api.post(
                'object', data=msgpack.packb(payload),
                headers={'Content-Type': self.api.content_type}
            ).content
            return msgpack.unpackb(result, raw=False)


class MsgPackClient(Client):
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

    def login(self, user, password):
        result = self.post('common', json=['login', self.database, user, password])
        if result.status_code == 200:
            self.uid = result.json()
            self.password = password
        else:
            raise ValueError('Error with user/password')
