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

features = c.common.check_for_features(['my_feature'])
databases = c.db.list()
report_id = c.report('account.invoice', [1])
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
 - http[s]+restapi
 - http[s]+msgpack
 - http[s]+xmlrpc
 - http[s]+xmlrpc-wst (XML-RPC with server transactions)

## Command-line interface

After installing the package, a `pygisceclient` command is available. This is useful for scripting and AI agent skills.

```
usage: pygisceclient [-h] --url URL --database DATABASE
                     (--token TOKEN | --user USER) [--password PASSWORD]
                     (--model MODEL | --service SERVICE) --method METHOD
                     [--service-auth {auto,raw,authenticated}]
                     [--args ARGS] [--kwargs KWARGS] [--no-verify]
```

### Options

| Option | Short | Description |
|---|---|---|
| `--url URL` | | Connection URL with protocol prefix |
| `--database DB` | `-d` | Database name |
| `--token TOKEN` | | Authentication token |
| `--user USER` | `-u` | Username |
| `--password PASS` | `-p` | Password (required with `--user`) |
| `--model MODEL` | `-m` | Model name (e.g. `res.users`) |
| `--service SERVICE` | `-s` | Service name (e.g. `common`, `db`, `report`) |
| `--method METHOD` | | Method name (e.g. `search`, `check_for_features`) |
| `--service-auth MODE` | | Auth mode for service calls: `auto`, `raw`, or `authenticated` |
| `--args JSON` | | Positional arguments as a JSON array (default `[]`) |
| `--kwargs JSON` | | Keyword arguments as a JSON object (default `{}`) |
| `--no-verify` | | Disable SSL certificate verification |

### Examples

Search for active users via XML-RPC:

```bash
pygisceclient \
  --url https+xmlrpc://erp.example.com \
  --database mydb \
  --user admin \
  --password secret \
  --model res.users \
  --method search \
  --args '[[["active", "=", true]]]'
```

Read specific fields via REST API using a token:

```bash
pygisceclient \
  --url https+restapi://erp.example.com \
  --database mydb \
  --token myapitoken \
  --model res.users \
  --method read \
  --args '[[1, 2, 3]]' \
  --kwargs '{"fields": ["name", "login"]}'
```

The result is printed as JSON to standard output.

Call a MsgPack service directly:

```bash
pygisceclient \
  --url https+msgpack://erp.example.com \
  --database mydb \
  --token myapitoken \
  --service common \
  --method check_for_features \
  --args '[["feature_a", "feature_b"]]'
```

Service calls use positional JSON arguments. By default, `common`, `db` and
`wc` are called raw because several of their methods do not receive `database`,
`uid` and `password`; other services are called authenticated. Use
`--service-auth raw` or `--service-auth authenticated` to force one mode.

## Standalone release binary

GitHub releases include a Linux x86_64 standalone CLI binary named
`pygisceclient-linux-x86_64`, plus its `.sha256` checksum. The binary is built
with PyInstaller during the automated release workflow.

The release binary can be used without installing the Python package:

```bash
chmod +x pygisceclient-linux-x86_64
./pygisceclient-linux-x86_64 --help
```

## Automated releases

Releases are generated from conventional commits merged into `main`.
`python-semantic-release` updates `setup.py`, creates the release commit and tag,
builds the source distribution with `python setup.py sdist`, and publishes the
GitHub release assets. The GitHub release upload includes both the `dist/*`
source distribution and the `release-assets/*` standalone CLI binary plus
checksum.

PyPI publishing uses `PYPI_TOKEN` when configured, falling back to the
organization-level `PYPI_MASTER_TOKEN`.
