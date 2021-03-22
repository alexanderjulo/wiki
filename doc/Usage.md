# Usage

## 1. Running wiki

Beheviour of wiki depend on environment variables, command line options and/or config files.

### 1.1. Environment variables
- `WIKI_HOST=...` - IP that wiki listens on (default 127.0.0.1; set 0.0.0.0 for everybody)
- `WIKI_PORT=...` - TCP port that wiki listens on (default 5000)
- `WIKI_DEBUG` - vebosity on

### 1.2. CLI options
Common wiki run as standalone application is:

    wiki [--directory=...] web [--host=...] [--port=...] [--debug]

Where:
- `--directory` - path of folder where config.py lives (default - current folder)
- `--host` - see `WIKI_HOST` above
- `--port` - see `WIKI_PORT` above
- `--debug` - see `WIKI_DEBUG` above

### 1.3. config.py

This file *must* exist and contains mostly optional definitions:

```python
SECRET_KEY = 'an unique and long key'        # mandatory
TITLE = 'Wiki title'                         # default 'wiki'
CONTENT_DIR = '/path/to/markdown/files/dir'  # default = --directory above
DEFAULT_AUTHENTICATION_METHOD='hash'         # 'hash' or 'cleartext' (default)
# PRIVATE=?                                  # don't know what is it
DEBUG = True                                 # default False
```

### 1.4. users.json

Users creditentials file is stored in CONTENT_DIR (right near *.md).
Sample of 1 user `user` with password `password` looks like:
```json
{
  "user": {
    "active": true,
    "roles": [],
    "authentication_method": "cleartext",
    "authenticated": true,
    "password": "password"
  }
}
```

### 1.5. Run from sources

To run wiki right in git clone dir:
```python
from wiki.web import create_app
app = create_app('/see/--directory/above')
app.run()   # add host=..., port=..., debug=...
```

## 2. Wiki features

### 2.1. Local URLs
- `[[Wiki Links]] stay [[wiki_link]] (lowercase and undescored)
- `[Ordinary links](Target File)` stay `<currentpage>/Target File.md`
- root page is exectly `home.md`
- folders and files right in CONTENT_DIR root connot be named as reserved actions:
  *home, index, create, edit, preview, move, delete, tags, tag, search, user*.

### 2.2. Importing *.md
You can just copy your existant *.md into CONTENT_DIR but with the only conditions:
- file *should* have *optional* [meta-data](https://python-markdown.github.io/extensions/meta_data/) lines `title: ...` and `tags: ...`
- file can be `Camel Case.md`, `Camel_Case.md`, `camel case.md` or `camel_case.md`, but `[[Wiki Link]]` will try to get `wiki_link.md` only.
