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
