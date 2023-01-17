# py-gisce-client

py-gisce-client is a Python client to access the [GISCE ERP](https://github.com/gisce/erp)

## Using REST API interface

```python
from gisce import RestApiClient as Client
url = 'http://localhost:5000'
user = 'admin'
password = 'admin'
c = Client(url, user=user, password=password)
users_obj = c.model('res.users')
```

## Using MsgPack API interface
```python
from gisce import MsgPackClient as Client
url = 'http://localhost:8068'
user = 'admin'
password = 'admin'
database = 'test'
c = Client(url, database=database, user=user, password=password)
users_obj = c.model('res.users')
```

## Using XML-RPC API interface
```python
from gisce import XmlRpcClient as Client
url = 'http://localhost:8069'
user = 'admin'
password = 'admin'
database = 'test'
c = Client(url, database=database, user=user, password=password)
users_obj = c.model('res.users')
```

## Using a single method
```python
from gisce import connect
url = 'http+xmlrpc://localhost:8069'
c = connect(url,'test', user='admin', password='agmin')
users_obj = c.model('res.users')
```

Where allowed protocols are:
 - http[s]+restpai
 - http[s]+msgpack
 - http[s]+xmlrpc
