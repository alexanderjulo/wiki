# Apache

Let's use wiki as WSGI application of Apache web-server.

Pre-conditions:

- Wiki is istalled as system-wide python3 library.
- data will be in `/var/lib/mynotes`.
- URL will be `http[s]://www.mysite.com/notes/`, so this will be WSGI application in virtual web-folder.
- RH-based Linux distro.

---

1. Apache config

    `/etc/httpd/conf.d/wiki.conf`:
    ```apache
    # don't forget 2 lines below to prevent non-ascii filenames error
    WSGIDaemonProcess apache lang=en_US.UTF-8 locale=C.UTF-8
    WSGIProcessGroup apache
    WSGIScriptAlias /notes /user/share/wiki/wiki.wsgi
    <Location /notes>
       Require all granted
    </Location>
    ```

1. WSGI app

    `/user/share/wiki/wiki.wsgi`:
    ```python
    #!/usr/bin/env python3
    import sys
    import logging
    from wiki.web import create_app
    
    logging.basicConfig(stream=sys.stderr)
    application = create_app("/etc/wiki/")
    ```

1. Wiki config

    `/etc/wiki/config.py`:
    ```python
    # encoding: utf-8
    SECRET_KEY='anuniqueandlongkey'
    TITLE='My Own Wiki'
    CONTENT_DIR='/var/lib/mynotes'
    ```

1. Wiki storage
    ```bash
    mkdir -p /var/lib/mynotes
    chown apache:apache /var/lib/mynotes
    ```

1. The end

    `sudo systemctl restart httpd` and goto `http://www.mysite.com/notes/`

---
*TODO: users.json, auth*
