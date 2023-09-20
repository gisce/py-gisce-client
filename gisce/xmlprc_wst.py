from .xmlrpc import XmlRpcClient, XmlRpcModel, ServerProxy


class XmlRpcWstModel(XmlRpcModel):
    def _call(self, method, *args, **kwargs):
        payload = (
            self.api.database,
            self.api.uid,
            self.api.password,
        )
        if self.api.tid:
            payload += (self.api.tid, )
        payload += (
            self._name,
            method
        ) + args
        return self.api.wst.execute(*payload)


class XmlRpcClientWst(XmlRpcClient):
    model_class = XmlRpcWstModel

    def __init__(self, url, database, token=None, user=None, password=None):
        super(XmlRpcClientWst, self).__init__(
            url, database, token, user, password
        )
        self.tid = None
        self.sync = ServerProxy(self.url + '/ws_transaction', allow_none=True)

    @property
    def wst(self):
        if self.tid:
            return self.sync
        else:
            return self.object

    def __enter__(self):
        self.begin()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.rollback()
        else:
            self.commit()
        self.close()

    def begin(self):
        self.tid = self.sync.begin(self.database, self.uid, self.password)

    def rollback(self):
        return self.sync.rollback(
            self.database, self.uid, self.password, self.tid
        )

    def commit(self):
        return self.sync.commit(
            self.database, self.uid, self.password, self.tid
        )

    def close(self):
        res = self.sync.close_connection(
            self.database, self.uid, self.password, self.tid
        )
        self.tid = None
        return res
