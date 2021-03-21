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
Wiki accepts almost any target in link definitions `[Link name](taget)`.  
Target name `target` stay `target.md` file.  
So target can be anything that OS/filesystem allows for filenames - `CamelCase With Spaces and non-ASCII 姓名`.  
Excepting these limitations:
- root page is exectly `home.md`
- folders and files right in CONTENT_DIR connot be named as reserved actions:
  *home, index, create, edit, preview, move, delete, tags, tag, search, user*.

### 2.2. Importing *.md
You can just copy your existant *.md into CONTENT_DIR but with the only (yet) conditions:
- file *must* have [meta-data](https://python-markdown.github.io/extensions/meta_data/) line `title: ...`
- and *can* have meta-data line `tags: ...`
