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

### Webservice transactions with XML-RPC

```python
from gisce import XmlRpcClientWst as Client
from gisce import XmlRpcClient as Client
url = 'http://localhost:8069'
user = 'admin'
password = 'admin'
database = 'test'
c = Client(url, database=database, user=user, password=password)
c.begin() # Start a new server transaction
users_obj = c.model('res.users')
users_obj.write([1], {'name': 'Fooo'})
c.commit() # or c.rollback()
c.close()
```

A `with_statement` is supported too

```python
with Client(url, database=database, user=user, password=password) as c:
    # All of this requests will use the same transaction
    users_obj = c.model('res.users')
    users_obj.write([1], {'name': 'Fooo'})

# on exit transaction will be rollbacked / commited if errors / no errors,
# and closed
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
 - http[s]+xmlrpc-wst (XML-RPC with server transactions)
