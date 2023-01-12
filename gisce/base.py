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


class Client(requests.Session):
    
    _cache_fields = {}
    model_class = None
    
    def __init__(self, url=None, token=None, user=None, password=None):
        super(Client, self).__init__()
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

    def request(self, method, url, *args, **kwargs):
        url = '/'.join([self.url, url])
        return super(Client, self).request(method, url, *args, **kwargs)

    def model(self, model):
        return self.model_class(model, self)

    def __getattr__(self, item):
        return self.model(to_dot(item))


class Model(object):

    def __init__(self, name, api):
        self._name = name
        self.api = api
        if not self.cache_fields:
            self.cache_fields = self.fields_get()
        self.browse_class = type(
            'BrowseRecord', (BrowseRecord, self.api.model_class), {}
        )

    @property
    def camelcase(self):
        return to_camel_case(self._name)

    @property
    def cache_fields(self):
        return self.api.__class__._cache_fields.get(self._name, {})

    @cache_fields.setter
    def cache_fields(self, value):
        self.api.__class__._cache_fields[self._name] = value

    def _call(self, method, *args, **kwargs):
        raise NotImplementedError

    def __getattr__(self, item):
        def wrapper(*args, **kwargs):
            return self._call(item, *args, **kwargs)
        return wrapper

    def browse(self, ids):
        if isinstance(ids, (tuple, list)):
            return [self.browse_class(self._name, self.api, x) for x in ids]
        else:
            return self.browse_class(self._name, self.api, ids)

    def __repr__(self):
        return '<{} {}>'.format(self.camelcase, self.api.url)


class BrowseRecord(Model):
    def __init__(self, name, api, id):
        super(BrowseRecord, self).__init__(name, api)
        self.id = id
        self.values = {}

    def __getattr__(self, item):

        if item not in self.cache_fields:
            def wrapper(*args, **kwargs):
                args = ([self.id],) + args
                parent = super(BrowseRecord, self).__getattr__(item)
                return parent(*args, **kwargs)
            return wrapper
        elif item not in self.values:
            result = self.read([item])[0][item]
            definition = self.cache_fields[item]
            if definition['type'] == 'many2one':
                result = self.browse_class(definition['relation'], self.api, result[0])
            elif definition['type'].endswith('2many'):
                result = [self.browse_class(definition['relation'], self.api, x) for x in result]
            self.values[item] = result
        return self.values.get(item)

    def __repr__(self):
        return '<BrowseRecord {}({}): {}>'.format(self._name, self.id, self.api.url)
