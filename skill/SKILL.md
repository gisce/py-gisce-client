---
name: gisce-erp
description: >-
  Interact with the GISCE ERP service (based on OpenERP) to query, create, update
  and delete records in any model. Use this skill whenever the user asks to read data
  from the ERP, modify ERP records, explore the ERP schema, run business methods,
  or integrate with the GISCE/OpenERP backend. Trigger keywords: ERP, GISCE, OpenERP,
  model, partner, invoice, factura, contract, pòlissa, comptador, meter, supply point,
  CUPS, search, read, write, create, unlink.
allowed-tools: shell bash
---

# GISCE ERP Client Skill

Use the `pygisceclient` CLI command to interact with the GISCE ERP.
Every call follows this pattern:

```bash
pygisceclient \
  --url <PROTOCOL_URL> \
  --database <DB> \
  --user <USER> --password <PASS> \
  --model <MODEL> \
  --method <METHOD> \
  --args '<JSON_ARRAY>' \
  --kwargs '<JSON_OBJECT>'
```

Output is always **JSON on stdout**. Errors go to stderr with a non-zero exit code.

---

## 1. Connection & Authentication

### Protocols

The `--url` must include a protocol prefix:

| Prefix | Transport |
|---|---|
| `https+restapi://` | REST API (Flask) |
| `https+msgpack://` | MsgPack API |
| `https+xmlrpc://` | XML-RPC |
| `https+xmlrpc-wst://` | XML-RPC with server transactions |

Use `http+…` variants for non-TLS connections. Add `--no-verify` to skip SSL certificate validation.

### Auth modes (mutually exclusive)

- **User/password**: `--user admin --password secret`
- **Token**: `--token <API_TOKEN>`

`--password` is required when `--user` is provided.

---

## 2. ERP Architecture Overview

The GISCE ERP uses an **ORM** layer over PostgreSQL. Every business entity is a **model** identified by a dotted name (e.g. `res.partner`, `account.invoice`). Models expose standard CRUD methods plus custom business logic. All protocols (REST, MsgPack, XML-RPC) dispatch through the same ORM pool, so the same models and methods are available regardless of protocol.

---

## 3. Standard ORM Methods

### `fields_get` — Discover the schema of a model

**Always call `fields_get` first** on any model you haven't seen before to learn which fields exist, their types, and constraints.

```bash
pygisceclient ... --model res.partner --method fields_get
```

Returns a dict mapping field names → definitions (`type`, `string`, `relation`, `required`, `readonly`, …).

Shortcut to list just the field names:

```bash
pygisceclient ... --model res.partner --method fields_get | jq 'keys'
```

### `search` — Find record IDs

```bash
pygisceclient ... --model res.partner --method search \
  --args '[[["active", "=", true], ["customer", "=", true]]]'
```

Positional args in order: `domain`, `offset` (int, default 0), `limit` (int), `order` (string), `context` (dict), `count` (bool).

Returns a JSON array of integer IDs (or a count if `count=true`).

### `search_count` — Count matching records

```bash
pygisceclient ... --model res.partner --method search_count \
  --args '[[["active", "=", true]]]'
```

### `read` — Fetch record data

```bash
pygisceclient ... --model res.partner --method read \
  --args '[[1, 2, 3], ["name", "vat", "city"]]'
```

Positional args: `ids` (list[int]), `fields` (list[str] or null for all).

Returns a list of dicts.

### `write` — Update records

```bash
pygisceclient ... --model res.partner --method write \
  --args '[[42], {"name": "New Name", "city": "Barcelona"}]'
```

Positional args: `ids` (list[int]), `vals` (dict). Returns `true`.

### `create` — Create a record

```bash
pygisceclient ... --model res.partner --method create \
  --args '[{"name": "ACME Corp", "customer": true}]'
```

Returns the new record's integer ID.

### `unlink` — Delete records

```bash
pygisceclient ... --model res.partner --method unlink \
  --args '[[42, 43]]'
```

### `name_get` — Human-readable names

```bash
pygisceclient ... --model res.partner --method name_get \
  --args '[[1, 2, 3]]'
```

Returns `[[id, "display name"], ...]`.

### `name_search` — Autocomplete search

```bash
pygisceclient ... --model res.partner --method name_search \
  --args '["Acme"]' \
  --kwargs '{"operator": "ilike", "limit": 10}'
```

### `exists` — Check if a record exists

```bash
pygisceclient ... --model res.partner --method exists \
  --args '[42]'
```

### Custom business methods

Models may expose methods beyond CRUD. Call them the same way:

```bash
pygisceclient ... --model account.invoice --method invoice_open \
  --args '[[42]]'
```

---

## 4. Domain Syntax (Search Filters)

Domains are lists of condition tuples following Polish (prefix) notation.

### Basic tuple

```
("field_name", "operator", value)
```

### Operators

| Operator | Description |
|---|---|
| `=`, `!=` | Equals / Not equals |
| `>`, `>=`, `<`, `<=` | Comparisons |
| `like`, `ilike` | SQL LIKE (case-sensitive / insensitive) |
| `not like`, `not ilike` | Negated variants |
| `in`, `not in` | Value in / not in list |
| `child_of` | Hierarchical descendant |

### Logical operators (prefix)

- `"&"` — AND (default, implicit between tuples)
- `"|"` — OR
- `"!"` — NOT (unary)

### Examples

Simple AND (implicit):
```json
[["active", "=", true], ["city", "ilike", "barcelona"]]
```

OR:
```json
["|", ["state", "=", "open"], ["state", "=", "draft"]]
```

Complex:
```json
["&", "|", ["type", "=", "out_invoice"], ["type", "=", "out_refund"], ["state", "=", "open"]]
```

---

## 5. Field Types

### Simple fields

| Type | Description |
|---|---|
| `char` | Short text (`VARCHAR`) |
| `text` | Long text |
| `integer` / `integer_big` | Integer / Big integer |
| `float` | Decimal (`NUMERIC`) |
| `boolean` | True/false |
| `date` / `datetime` / `time` | Temporal types |
| `binary` | Binary data |
| `selection` | Enumeration |
| `json` / `jsonb` | JSON data |

### Relational fields

| Type | Read returns | Write with |
|---|---|---|
| `many2one` | `[id, "name"]` or `false` | integer ID |
| `one2many` | list of IDs | special tuples (see below) |
| `many2many` | list of IDs | special tuples (see below) |
| `reference` | `"model,id"` string | `"model,id"` string |

### Writing relational fields (one2many / many2many)

Use special tuple commands in `write`/`create` vals:

| Command | Meaning |
|---|---|
| `[0, 0, {vals}]` | Create new related record |
| `[1, id, {vals}]` | Update existing related record |
| `[2, id, 0]` | Delete related record |
| `[3, id, 0]` | Unlink (remove relation, keep record) |
| `[4, id, 0]` | Link an existing record |
| `[5, 0, 0]` | Unlink all |
| `[6, 0, [ids]]` | Replace all with given list |

### Functional / computed fields

- `function`: Computed by Python; may or may not be stored.
- `related`: Follows a chain of relations.
- `property`: Per-company configurable value.

---

## 6. Common Workflow Patterns

### Discover a model's schema

```bash
pygisceclient ... --model res.partner --method fields_get | jq 'keys'
```

### Search + Read

```bash
IDS=$(pygisceclient ... --model res.partner --method search \
  --args '[[["customer", "=", true]]]')

pygisceclient ... --model res.partner --method read \
  --args "[$IDS, [\"name\", \"vat\", \"city\"]]"
```

### Paginated search

```bash
pygisceclient ... --model account.invoice --method search \
  --args '[[["state", "=", "open"]], 0, 100, "date_invoice desc"]'
```

### Count before reading

```bash
pygisceclient ... --model res.partner --method search_count \
  --args '[[["active", "=", true]]]'
```

### Discover all installed models

```bash
MODEL_IDS=$(pygisceclient ... --model ir.model --method search --args '[[]]')
pygisceclient ... --model ir.model --method read \
  --args "[$MODEL_IDS, [\"model\", \"name\"]]"
```

### Discover fields via ir.model.fields

```bash
FIELD_IDS=$(pygisceclient ... --model ir.model.fields --method search \
  --args '[[["model", "=", "res.partner"]]]')
pygisceclient ... --model ir.model.fields --method read \
  --args "[$FIELD_IDS, [\"name\", \"field_description\", \"ttype\", \"relation\", \"required\", \"readonly\"]]"
```

---

## 7. Core Base Models

These models are always available:

| Model | Description |
|---|---|
| `res.partner` | Contacts, companies, addresses |
| `res.users` | System users |
| `res.company` | Companies |
| `res.country` | Countries |
| `res.country.state` | States / provinces |
| `res.currency` | Currencies |
| `ir.model` | Model registry (all installed models) |
| `ir.model.fields` | Field definitions for all models |
| `ir.model.access` | Access control entries |
| `ir.rule` | Record-level security rules |
| `ir.sequence` | Sequence generators |
| `ir.attachment` | File attachments |
| `ir.cron` | Scheduled actions |
| `account.invoice` | Invoices |
| `account.invoice.line` | Invoice lines |
| `account.account` | Chart of accounts |
| `product.product` | Products |
| `sale.order` | Sale orders |
| `purchase.order` | Purchase orders |
| `stock.picking` | Stock movements |

---

## 8. Best Practices

1. **Always discover the schema first** — call `fields_get` on a model before reading or writing.
2. **Paginate large results** — use `offset` and `limit` in `search`. Process in batches of 1000.
3. **Request only needed fields** — pass an explicit field list to `read`.
4. **Use `search_count`** before large reads to know how many records match.
5. **Relational field values** — `many2one` returns `[id, "name"]` on read; write with just the integer ID. `one2many`/`many2many` return lists of IDs.
6. **JSON escaping** — `--args` and `--kwargs` expect valid JSON. Use single quotes around JSON to avoid shell escaping issues.
7. **Error handling** — non-zero exit codes mean failure; error message is on stderr.
8. **Security** — the ERP enforces access control. Operations may fail with `AccessError` if the user lacks permissions.
