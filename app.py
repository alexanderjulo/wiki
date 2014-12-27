import binascii
import hashlib
import os
import re
import markdown
import json
from functools import wraps
from flask import (Flask, render_template, flash, redirect, url_for, request,
                   abort)
from flask.ext.wtf import Form
from wtforms import (BooleanField, TextField, TextAreaField, PasswordField)
from wtforms.validators import (InputRequired, ValidationError)
from flask.ext.login import (LoginManager, login_required, current_user,
                             login_user, logout_user)
from flask.ext.script import Manager


"""
    Application Setup
    ~~~~~~~~~
"""

app = Flask(__name__)
app.config['CONTENT_DIR'] = 'content'
app.config['TITLE'] = 'wiki'
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



"""
    Wiki classes
    ~~~~~~~~~~~~
"""


class Processors(object):
    """This class is collection of processors for various content items.
    """
    def __init__(self, content=""):
        """Initialization function.  Runs Processors().pre() on content.

        Args:
            None

        Kwargs:
            content (str): Preprocessed content directly from the file or
            textarea.
        """
        self.content = self.pre(content)

    def wikilink(self, html):
        """Processes Wikilink syntax "[[Link]]" within content body.  This is
        intended to be run after the content has been processed by Markdown.

        Args:
            html (str): Post-processed HTML output from Markdown

        Kwargs:
            None

        Syntax: This accepts Wikilink syntax in the form of [[WikiLink]] or
        [[url/location|LinkName]].  Everything is referenced from the base
        location "/", therefore sub-pages need to use the
        [[page/subpage|Subpage]].
        """
        link = r"((?<!\<code\>)\[\[([^<].+?) \s*([|] \s* (.+?) \s*)?]])"
        compLink = re.compile(link, re.X | re.U)
        for i in compLink.findall(html):
            title = [i[-1] if i[-1] else i[1]][0]
            url = self.clean_url(i[1])
            formattedLink = u"<a href='{0}'>{1}</a>".format(url_for('display', url=url), title)
            html = re.sub(compLink, formattedLink, html, count=1)
        return html

    def clean_url(self, url):
        """Cleans the url and corrects various errors.  Removes multiple spaces
        and all leading and trailing spaces.  Changes spaces to underscores and
        makes all characters lowercase.  Also takes care of Windows style
        folders use.

        Args:
            url (str): URL link

        Kwargs:
            None
        """
        pageStub = re.sub('[ ]{2,}', ' ', url).strip()
        pageStub = pageStub.lower().replace(' ', '_')
        pageStub = pageStub.replace('\\\\', '/').replace('\\', '/')
        return pageStub

    def pre(self, content):
        """Content preprocessor.  This currently does nothing.

        Args:
            content (str): Preprocessed content directly from the file or
            textarea.

        Kwargs:
            None
        """
        return content

    def post(self, html):
        """Content post-processor.

        Args:
            html (str): Post-processed HTML output from Markdown

        Kwargs:
            None
        """
        return self.wikilink(html)

    def out(self):
        """Final content output.  Processes the Markdown, post-processes, and
        Meta data.
        """
        md = markdown.Markdown(['codehilite', 'fenced_code', 'meta', 'tables'])
        html = md.convert(self.content)
        phtml = self.post(html)
        body = self.content.split('\n\n', 1)[1]
        meta = md.Meta
        return phtml, body, meta


class Page(object):
    def __init__(self, path, url, new=False):
        self.path = path
        self.url = url
        self._meta = {}
        if not new:
            self.load()
            self.render()

    def load(self):
        with open(self.path, 'rU') as f:
            self.content = f.read().decode('utf-8')

    def render(self):
        processed = Processors(self.content)
        self._html, self.body, self._meta = processed.out()

    def save(self, update=True):
        folder = os.path.dirname(self.path)
        if not os.path.exists(folder):
            os.makedirs(folder)
        with open(self.path, 'w') as f:
            for key, value in self._meta.items():
                line = u'%s: %s\n' % (key, value)
                f.write(line.encode('utf-8'))
            f.write('\n'.encode('utf-8'))
            f.write(self.body.replace('\r\n', '\n').encode('utf-8'))
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
        try:
            return self['title']
        except KeyError:
            return self.url

    @title.setter
    def title(self, value):
        self['title'] = value

    @property
    def tags(self):
        try:
            return self['tags']
        except KeyError:
            return ""

    @tags.setter
    def tags(self, value):
        self['tags'] = value


class Wiki(object):
    def __init__(self, root):
        self.root = root

    def path(self, url):
        return os.path.join(self.root, url + '.md')

    def exists(self, url):
        path = self.path(url)
        return os.path.exists(path)

    def get(self, url):
        path = os.path.join(self.root, url + '.md')
        if self.exists(url):
            return Page(path, url)
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
        return Page(path, url, new=True)

    def move(self, url, newurl):
        os.rename(
            os.path.join(self.root, url) + '.md',
            os.path.join(self.root, newurl) + '.md'
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
                elif name.endswith('.md'):
                    if not path_prefix:
                        url = name[:-3]
                    else:
                        url = os.path.join(path_prefix[0], name[:-3])
                    if attr:
                        pages[getattr(page, attr)] = page  # TODO: looks like bug, but doesn't appear to be used
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

    def search(self, term, ignore_case=True, attrs=['title', 'tags', 'body']):
        pages = self.index()
        regex = re.compile(term, re.IGNORECASE if ignore_case else 0)
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
    url = TextField('', [InputRequired()])

    def validate_url(form, field):
        if wiki.exists(field.data):
            raise ValidationError('The URL "%s" exists already.' % field.data)

    def clean_url(self, url):
        return Processors().clean_url(url)


class SearchForm(Form):
    term = TextField('', [InputRequired()])
    ignore_case = BooleanField(description='Ignore Case', default=app.config.get('DEFAULT_SEARCH_IGNORE_CASE', True))


class EditorForm(Form):
    title = TextField('', [InputRequired()])
    body = TextAreaField('', [InputRequired()])
    tags = TextField('')


class LoginForm(Form):
    name = TextField('', [InputRequired()])
    password = PasswordField('', [InputRequired()])

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


wiki = Wiki(app.config.get('CONTENT_DIR'))

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
    return render_template('editor.html', form=form, page=page)


@app.route('/preview/', methods=['POST'])
@protect
def preview():
    a = request.form
    data = {}
    processed = Processors(a['body'])
    data['html'], data['body'], data['meta'] = processed.out()
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
        results = wiki.search(form.term.data, form.ignore_case.data)
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


"""
    Error Handlers
    ~~~~~~~~~~~~~~
"""


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


if __name__ == '__main__':
    manager.run()
