import requests
from . import __version__

USER_AGENT = "PyGisceClient/Python"
VERSION = __version__
DEBUG = False
if DEBUG:
    import logging
    logging.basicConfig(level=logging.DEBUG)


class ApiException(Exception):
    pass


def to_camel_case(model):
    words = model.split('.')
    camel_case = words[0].title() + ''.join(word.capitalize() for word in words[1:])
    return camel_case


def to_dot(name):
    """
    Converts a model name from _ to .
    :param name: Module name
    :return: Module name converted
    """
    import re
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1.\2', name)
    return re.sub('([a-z])([A-Z0-9])', r'\1.\2', s1).lower()


class BaseClient(object):

    model_class = None

    def __init__(self):
        self._cache_fields = {}
        self.models = []

    def __getattr__(self, item):
        return self.model(to_dot(item))

    def model(self, model):
        if self.models and model not in self.models:
            raise Exception("Model '{}' not found".format(model))
        return self.model_class(model, self)


class RequestsClient(requests.Session, BaseClient):
    
    def __init__(self, url=None, token=None, user=None, password=None):
        super(RequestsClient, self).__init__()
        self.headers.update({
            'User-Agent': '{}/{}'.format(USER_AGENT, VERSION)
        })
        if user and password:
            self.auth = (user, password)
        elif token:
            self.headers.update({
                'Authorization': 'token {}'.format(token)
            })
        else:
            raise Exception('User/password or token must be passed')
        self.url = url
        self._cache_fields = {}

    def request(self, method, url, *args, **kwargs):
        url = '/'.join([self.url, url])
        return super(RequestsClient, self).request(method, url, *args, **kwargs)


class Model(object):

    def __init__(self, name, api):
        self._name = name
        self.api = api
        if not self.cache_fields:
            self.cache_fields = self.fields_get()

    @property
    def client(self):
        return self.api

    @property
    def camelcase(self):
        return to_camel_case(self._name)

    @property
    def cache_fields(self):
        return self.api._cache_fields.get(self._name, {})

    @cache_fields.setter
    def cache_fields(self, value):
        self.api._cache_fields[self._name] = value

    def _call(self, method, *args, **kwargs):
        raise NotImplementedError

    def __getattr__(self, item):
        def wrapper(*args, **kwargs):
            return self._call(item, *args, **kwargs)
        return wrapper

    def browse(self, ids):
        if isinstance(ids, (tuple, list)):
            return [BrowseRecord(self, x) for x in ids]
        else:
            return BrowseRecord(self, ids)

    def __repr__(self):
        return '<{} {}>'.format(self.camelcase, self.api.url)


class PositionArgumentsModel(Model):

    def search(self, args, offset=0, limit=None, order=None,
               context=None, count=False):
        return self._call(
            'search', args, offset, limit, order, context, count
        )

    def create(self, vals, context=None):
        res_id = self._call('create', vals, context)
        return self.browse(res_id)

    def read(self, ids, fields=None, context=None, load='_classic_read'):
        return self._call('read', ids, fields, context, load)

    def __getattr__(self, item):
        def wrapper(*args, **kwargs):
            context = kwargs.pop('context', None)
            if context:
                args = args + (context, )
            return self._call(item, *args, **kwargs)
        return wrapper


class BrowseRecord(object):
    def __init__(self, model, res_id):
        self._model = model
        self.id = res_id
        self._values = {}

    def __getattr__(self, item):
        if item not in self._model.cache_fields:
            def wrapper(*args, **kwargs):
                args = ([self.id],) + args
                return getattr(self._model, item)(*args, **kwargs)
            return wrapper
        elif item not in self._values:
            result = self.read([item])[0][item]
            definition = self._model.cache_fields[item]
            if 'relation' in definition:
                obj = self._model.api.model(definition['relation'])
                if definition['type'] == 'many2one':
                    if result:
                        result = obj.browse(result[0])
                elif definition['type'].endswith('2many'):
                    result = [obj.browse(x) for x in result]
            self._values[item] = result
        return self._values.get(item)

    def __repr__(self):
        return '<{} {}({}): {}>'.format(
            self.__class__.__name__,
            self._model._name,
            self.id, self._model.api.url
        )
