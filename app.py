# -*- coding: utf-8 -*-
import binascii
import hashlib
import os
import re
import textwrap
import markdown
import docutils.core
import docutils.io
import json
from functools import wraps
from flask import (Flask, render_template, flash, redirect, url_for, request,
                   abort)
from flask.ext.wtf import (Form, TextField, TextAreaField, PasswordField,
                           Required, ValidationError)
from flask.ext.login import (LoginManager, login_required, current_user,
                             login_user, logout_user)
from flask.ext.script import Manager


"""
    Markup classes
    ~~~~~~~~~~~~~~
"""

class Markup(object):
    """ Base markup class."""
    NAME = 'Text'
    META_LINE = '%s: %s\n'
    EXTENSION = '.txt'
    HOWTO = """ """

    def __init__(self, raw_content):
        self.raw_content = raw_content

    def process(self):
        """
        return (html, body, meta) where HTML is the rendered output
        body is the the editable content (text), and meta is
        a dictionary with at least ['title', 'tags'] keys
        """
        raise NotImplementedError("override in a subclass")

    @classmethod
    def howto(cls):
        return cls(textwrap.dedent(cls.HOWTO)).process()[0]


class Markdown(Markup):
    NAME = 'markdown'
    META_LINE = '%s: %s\n'
    EXTENSION = '.md'
    HOWTO = """
        This editor is [markdown][] featured.

            * I am
            * a
            * list

        Turns into:

        * I am
        * a
        * list

        `**bold** and *italics*` turn into **bold** and *italics*. Very easy!

        Create links with `[Wiki](http://github.com/alexex/wiki)`. They turn into
        [Wiki][].

        Headers are as follows:

            # Level 1
            ## Level 2
            ### Level 3

        [markdown]: http://daringfireball.net/projects/markdown/
        [Wiki]: http://github.com/alexex/wiki
        """


    def process(self):
        # Processes Markdown text to HTML, returns original markdown text,
        # and adds meta
        md = markdown.Markdown(['codehilite', 'fenced_code', 'meta'])
        html = md.convert(self.raw_content)
        meta_lines, body = self.raw_content.split('\n\n', 1)
        meta = md.Meta
        return html, body, meta


class RestructuredText(Markup):
    NAME = 'restructuredtext'
    META_LINE = '.. %s: %s\n'
    EXTENSION = '.rst'
    HOWTO = """
        This editor is `reStructuredText`_ featured::

            * I am
            * a
            * list

        Turns into:

        *  I am
        *  a
        *  list

        ``**bold** and *italics*`` turn into **bold** and *italics*. Very easy!

        Create links with ```Wiki <http://github.com/alexex/wiki>`_``. They turn into
        `Wiki <https://github.com/alexex/wiki>`_.

        Headers are just any underline (and, optionally, overline). For example::

            Level 1
            *******

            Level 2
            -------

            Level 3
            +++++++

        .. _reStructuredText: http://docutils.sourceforge.net/rst.html
        """

    def process(self):
        settings = {'initial_header_level': 2,
                    'record_dependencies': True,
                    'stylesheet_path': None,
                    'link_stylesheet': True,
                    'syntax_highlight': 'short',
                    }
        html, _, deps = self._rst2html(self.raw_content, settings_overrides=settings)
        meta_lines, body = self.raw_content.split('\n\n', 1)
        meta = self._parse_meta(meta_lines.split('\n'))
        return html, body, meta

    def _rst2html(self, source, source_path=None, source_class=docutils.io.StringInput,
                  destination_path=None, reader=None, reader_name='standalone',
                  parser=None, parser_name='restructuredtext', writer=None,
                  writer_name='html', settings=None, settings_spec=None,
                  settings_overrides=None, config_section=None,
                  enable_exit_status=None):
        # Taken from Nikola
        # http://bit.ly/14CmQyh
        output, pub = docutils.core.publish_programmatically(
            source=source, source_path=source_path, source_class=source_class,
            destination_class=docutils.io.StringOutput,
            destination=None, destination_path=destination_path,
            reader=reader, reader_name=reader_name,
            parser=parser, parser_name=parser_name,
            writer=writer, writer_name=writer_name,
            settings=settings, settings_spec=settings_spec,
            settings_overrides=settings_overrides,
            config_section=config_section,
            enable_exit_status=enable_exit_status)
        return (pub.writer.parts['fragment'], pub.document.reporter.max_level,
                pub.settings.record_dependencies)


    def _parse_meta(self, lines):
        """ Parse Meta-Data. Taken from Python-Markdown"""
        META_RE = re.compile(r'^\.\.\s(?P<key>.*?): (?P<value>.*)')
        meta = {}
        key = None
        for line in lines:
            if line.strip() == '':
                continue
            m1 = META_RE.match(line)
            if m1:
                key = m1.group('key').lower().strip()
                value = m1.group('value').strip()
                try:
                    meta[key].append(value)
                except KeyError:
                    meta[key] = [value]
        return meta



"""
    Wiki classes
    ~~~~~~~~~~~~
"""
class Page(object):
    def __init__(self, path, url, new=False, markup=Markdown):
        self.path = path
        self.url = url
        self.markup = markup
        self._meta = {}
        if not new:
            self.load()
            self.render()

    def load(self):
        with open(self.path, 'rU') as f:
            self.content = self.markup(f.read().decode('utf-8'))

    def render(self):
        self._html, self.body, self._meta = self.content.process()

    def save(self, update=True):
        folder = os.path.dirname(self.path)
        if not os.path.exists(folder):
            os.makedirs(folder)
        with open(self.path, 'w') as f:
            for key, value in self._meta.items():
                line = self.markup.META_LINE % (key, value)
                f.write(line.encode('utf-8'))
            f.write('\n'.encode('utf-8'))
            f.write(self.body.replace('\r\n', os.linesep).encode('utf-8'))
        if update:
            self.load()
            self.render()

    @property
    def meta(self):
        return self._meta

    def __getitem__(self, name):
        item = self._meta[name]
        if len(item) == 1:
            return item[0]
        print item
        return item

    def __setitem__(self, name, value):
        self._meta[name] = value

    @property
    def html(self):
        return self._html

    def __html__(self):
        return self.html

    @property
    def title(self):
        return self['title']

    @title.setter               # NOQA
    def title(self, value):
        self['title'] = value

    @property
    def tags(self):
        return self['tags']

    @tags.setter               # NOQA
    def tags(self, value):
        self['tags'] = value


class Wiki(object):
    def __init__(self, root, markup=Markdown):
        self.root = root
        self.markup = markup

    def path(self, url):
        return os.path.join(self.root, url + self.markup.EXTENSION)

    def exists(self, url):
        path = self.path(url)
        return os.path.exists(path)

    def get(self, url):
        path = os.path.join(self.root, url + self.markup.EXTENSION)
        if self.exists(url):
            return Page(path, url, markup=self.markup)
        return None

    def get_or_404(self, url):
        page = self.get(url)
        if page:
            return page
        abort(404)

    def get_bare(self, url):
        path = self.path(url)
        if self.exists(url):
            return False
        return Page(path, url, new=True, markup=self.markup)

    def move(self, url, newurl):
        os.rename(
            os.path.join(self.root, url) + self.markup.EXTENSION,
            os.path.join(self.root, newurl) + self.markup.EXTENSION
        )

    def delete(self, url):
        path = self.path(url)
        if not self.exists(url):
            return False
        print path
        os.remove(path)
        return True

    def index(self, attr=None):
        def _walk(directory, path_prefix=()):
            for name in os.listdir(directory):
                fullname = os.path.join(directory, name)
                if os.path.isdir(fullname):
                    _walk(fullname, path_prefix + (name,))
                elif name.endswith(self.markup.EXTENSION):
                    if not path_prefix:
                        url = name[:-3]
                    else:
                        url = os.path.join(path_prefix[0], name[:-3])
                    if attr:
                        pages[getattr(page, attr)] = page
                    else:
                        pages.append(Page(fullname, url.replace('\\', '/')))
        if attr:
            pages = {}
        else:
            pages = []
        _walk(self.root)
        if not attr:
            return sorted(pages, key=lambda x: x.title.lower())
        return pages

    def get_by_title(self, title):
        pages = self.index(attr='title')
        return pages.get(title)

    def get_tags(self):
        pages = self.index()
        tags = {}
        for page in pages:
            pagetags = page.tags.split(',')
            for tag in pagetags:
                tag = tag.strip()
                if tag == '':
                    continue
                elif tags.get(tag):
                    tags[tag].append(page)
                else:
                    tags[tag] = [page]
        return tags

    def index_by_tag(self, tag):
        pages = self.index()
        tagged = []
        for page in pages:
            if tag in page.tags:
                tagged.append(page)
        return sorted(tagged, key=lambda x: x.title.lower())

    def search(self, term, attrs=['title', 'tags', 'body']):
        pages = self.index()
        regex = re.compile(term)
        matched = []
        for page in pages:
            for attr in attrs:
                if regex.search(getattr(page, attr)):
                    matched.append(page)
                    break
        return matched


"""
    User classes & helpers
    ~~~~~~~~~~~~~~~~~~~~~~
"""


class UserManager(object):
    """A very simple user Manager, that saves it's data as json."""
    def __init__(self, path):
        self.file = os.path.join(path, 'users.json')

    def read(self):
        if not os.path.exists(self.file):
            return {}
        with open(self.file) as f:
            data = json.loads(f.read())
        return data

    def write(self, data):
        with open(self.file, 'w') as f:
            f.write(json.dumps(data, indent=2))

    def add_user(self, name, password,
                 active=True, roles=[], authentication_method=None):
        users = self.read()
        if users.get(name):
            return False
        if authentication_method is None:
            authentication_method = get_default_authentication_method()
        new_user = {
            'active': active,
            'roles': roles,
            'authentication_method': authentication_method,
            'authenticated': False
        }
        # Currently we have only two authentication_methods: cleartext and
        # hash. If we get more authentication_methods, we will need to go to a
        # strategy object pattern that operates on User.data.
        if authentication_method == 'hash':
            new_user['hash'] = make_salted_hash(password)
        elif authentication_method == 'cleartext':
            new_user['password'] = password
        else:
            raise NotImplementedError(authentication_method)
        users[name] = new_user
        self.write(users)
        userdata = users.get(name)
        return User(self, name, userdata)

    def get_user(self, name):
        users = self.read()
        userdata = users.get(name)
        if not userdata:
            return None
        return User(self, name, userdata)

    def delete_user(self, name):
        users = self.read()
        if not users.pop(name, False):
            return False
        self.write(users)
        return True

    def update(self, name, userdata):
        data = self.read()
        data[name] = userdata
        self.write(data)


class User(object):
    def __init__(self, manager, name, data):
        self.manager = manager
        self.name = name
        self.data = data

    def get(self, option):
        return self.data.get(option)

    def set(self, option, value):
        self.data[option] = value
        self.save()

    def save(self):
        self.manager.update(self.name, self.data)

    def is_authenticated(self):
        return self.data.get('authenticated')

    def is_active(self):
        return self.data.get('active')

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.name

    def check_password(self, password):
        """Return True, return False, or raise NotImplementedError if the
        authentication_method is missing or unknown."""
        authentication_method = self.data.get('authentication_method', None)
        if authentication_method is None:
            authentication_method = get_default_authentication_method()
        # See comment in UserManager.add_user about authentication_method.
        if authentication_method == 'hash':
            result = check_hashed_password(password, self.get('hash'))
        elif authentication_method == 'cleartext':
            result = (self.get('password') == password)
        else:
            raise NotImplementedError(authentication_method)
        return result


def get_default_authentication_method():
    return app.config.get('DEFAULT_AUTHENTICATION_METHOD', 'cleartext')


def make_salted_hash(password, salt=None):
    if not salt:
        salt = os.urandom(64)
    d = hashlib.sha512()
    d.update(salt[:32])
    d.update(password)
    d.update(salt[32:])
    return binascii.hexlify(salt) + d.hexdigest()


def check_hashed_password(password, salted_hash):
    salt = binascii.unhexlify(salted_hash[:128])
    return make_salted_hash(password, salt) == salted_hash


def protect(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if app.config.get('PRIVATE') and not current_user.is_authenticated():
            return loginmanager.unauthorized()
        return f(*args, **kwargs)
    return wrapper


"""
    Forms
    ~~~~~
"""


class URLForm(Form):
    url = TextField('', [Required()])

    def validate_url(form, field):
        if wiki.exists(field.data):
            raise ValidationError('The URL "%s" exists already.' % field.data)

    def clean_url(self, url):
        # Cleans the url and corrects various errors.
        # Remove multiple spaces and leading and trailing spaces
        pageStub = re.sub('[ ]{2,}', ' ', url).strip()
        # Changes spaces to underscores and make everything lowercase
        pageStub = pageStub.lower().replace(' ', '_')
        # Corrects Windows style folders
        pageStub = pageStub.replace('\\\\', '/').replace('\\', '/')
        return pageStub


class SearchForm(Form):
    term = TextField('', [Required()])


class EditorForm(Form):
    title = TextField('', [Required()])
    body = TextAreaField('', [Required()])
    tags = TextField('')


class LoginForm(Form):
    name = TextField('', [Required()])
    password = PasswordField('', [Required()])

    def validate_name(form, field):
        user = users.get_user(field.data)
        if not user:
            raise ValidationError('This username does not exist.')

    def validate_password(form, field):
        user = users.get_user(form.name.data)
        if not user:
            return
        if not user.check_password(field.data):
            raise ValidationError('Username and password do not match.')


"""
    Application Setup
    ~~~~~~~~~
"""

app = Flask(__name__)
app.debug = True
app.config['CONTENT_DIR'] = 'content'
app.config['TITLE'] = 'wiki'
app.config['MARKUP'] = 'markdown'  # or 'restructucturedtext'
try:
    app.config.from_pyfile(
        os.path.join(app.config.get('CONTENT_DIR'), 'config.py')
    )
except IOError:
    print ("Startup Failure: You need to place a "
           "config.py in your content directory.")

manager = Manager(app)

loginmanager = LoginManager()
loginmanager.init_app(app)
loginmanager.login_view = 'user_login'
markup = dict([(klass.NAME, klass) for klass in
               Markup.__subclasses__()])[app.config.get('MARKUP')]
wiki = Wiki(app.config.get('CONTENT_DIR'), markup)

users = UserManager(app.config.get('CONTENT_DIR'))


@loginmanager.user_loader
def load_user(name):
    return users.get_user(name)


"""
    Routes
    ~~~~~~
"""


@app.route('/')
@protect
def home():
    page = wiki.get('home')
    if page:
        return display('home')
    return render_template('home.html')


@app.route('/index/')
@protect
def index():
    pages = wiki.index()
    return render_template('index.html', pages=pages)


@app.route('/<path:url>/')
@protect
def display(url):
    page = wiki.get_or_404(url)
    return render_template('page.html', page=page)


@app.route('/create/', methods=['GET', 'POST'])
@protect
def create():
    form = URLForm()
    if form.validate_on_submit():
        return redirect(url_for('edit', url=form.clean_url(form.url.data)))
    return render_template('create.html', form=form)


@app.route('/edit/<path:url>/', methods=['GET', 'POST'])
@protect
def edit(url):
    page = wiki.get(url)
    form = EditorForm(obj=page)
    if form.validate_on_submit():
        if not page:
            page = wiki.get_bare(url)
        form.populate_obj(page)
        page.save()
        flash('"%s" was saved.' % page.title, 'success')
        return redirect(url_for('display', url=url))
    return render_template('editor.html', form=form, page=page,
                           markup=markup)


@app.route('/preview/', methods=['POST'])
@protect
def preview():
    a = request.form
    data = {}
    data['html'], data['body'], data['meta'] = markup(a['body']).process()
    return data['html']


@app.route('/move/<path:url>/', methods=['GET', 'POST'])
@protect
def move(url):
    page = wiki.get_or_404(url)
    form = URLForm(obj=page)
    if form.validate_on_submit():
        newurl = form.url.data
        wiki.move(url, newurl)
        return redirect(url_for('.display', url=newurl))
    return render_template('move.html', form=form, page=page)


@app.route('/delete/<path:url>/')
@protect
def delete(url):
    page = wiki.get_or_404(url)
    wiki.delete(url)
    flash('Page "%s" was deleted.' % page.title, 'success')
    return redirect(url_for('home'))


@app.route('/tags/')
@protect
def tags():
    tags = wiki.get_tags()
    return render_template('tags.html', tags=tags)


@app.route('/tag/<string:name>/')
@protect
def tag(name):
    tagged = wiki.index_by_tag(name)
    return render_template('tag.html', pages=tagged, tag=name)


@app.route('/search/', methods=['GET', 'POST'])
@protect
def search():
    form = SearchForm()
    if form.validate_on_submit():
        results = wiki.search(form.term.data)
        return render_template('search.html', form=form,
                               results=results, search=form.term.data)
    return render_template('search.html', form=form, search=None)


@app.route('/user/login/', methods=['GET', 'POST'])
def user_login():
    form = LoginForm()
    if form.validate_on_submit():
        user = users.get_user(form.name.data)
        login_user(user)
        user.set('authenticated', True)
        flash('Login successful.', 'success')
        return redirect(request.args.get("next") or url_for('index'))
    return render_template('login.html', form=form)


@app.route('/user/logout/')
@login_required
def user_logout():
    current_user.set('authenticated', False)
    logout_user()
    flash('Logout successful.', 'success')
    return redirect(url_for('index'))


@app.route('/user/')
def user_index():
    pass


@app.route('/user/create/')
def user_create():
    pass


@app.route('/user/<int:user_id>/')
def user_admin(user_id):
    pass


@app.route('/user/delete/<int:user_id>/')
def user_delete(user_id):
    pass


if __name__ == '__main__':
    manager.run()
