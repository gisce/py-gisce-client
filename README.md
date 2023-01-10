# py-gisce-client

py-gisce-client is a Python client to access the [GISCE ERP](https://github.com/gisce/erp)

```python
from gisce import Client
url = 'http://localhost:5000'
user = 'admin'
password = 'admin'
c = Client(url, user=user, password=password)
users_obj = c.model('res.users')
```