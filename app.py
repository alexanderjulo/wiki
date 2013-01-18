import os
import re
import markdown
import json
from functools import wraps
from flask import Flask, render_template, flash, redirect, url_for, request, \
abort
from flask.ext.wtf import Form, TextField, TextAreaField, PasswordField, \
Required, ValidationError
from flask.ext.login import LoginManager, login_required, current_user, \
login_user, logout_user



"""
	Wiki classes
	~~~~~~~~~~~~
"""

class Page(object):
	def __init__(self, path, url, new=False):
		self.path = path
		self.url = url
		self._meta = {}
		if not new:
			self.load()
			self.render()

	def load(self):
		with open(self.path) as f:
			self.content = f.read().decode('utf-8')

	def render(self):
		md = markdown.Markdown(['codehilite', 'fenced_code', 'meta'])
		self._html = md.convert(self.content)
		self.body = self.content.split('\n\n')[1]
		self._meta = md.Meta

	def save(self, update=True):
		folder = '/'.join(os.path.join(self.path).split('/')[:-1])
		if not os.path.exists(folder):
			os.makedirs(folder)
		with open(self.path, 'w') as f:
			for key, value in self._meta.items():
				f.write('%s: %s\n'.encode('utf-8') % (key, value))
			f.write('\n'.encode('utf-8'))
			f.write(self.body.encode('utf-8'))
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

	@title.setter
	def title(self, value):
		self['title'] = value

	@property
	def tags(self):
		return self['tags']

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
						pages[getattr(page, attr)] = page
					else: 
						pages.append(Page(fullname, url))
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

	def add_user(self, name, password, active=True, roles=[]):
		users = self.read()
		if users.get(name):
			return False
		users[name] = {
			'password': password,
			'active': active,
			'roles': roles,
			'authenticated': False
		}
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
		if not self.pop(name):
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

class CreateForm(Form):
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
		if not field.data == user.get('password'):
			raise ValidationError('Username and password do not match.')



"""
	Application Setup
	~~~~~~~~~
"""

app = Flask(__name__)
app.config['CONTENT_DIR'] = 'content'
try:
	app.config.from_pyfile(os.path.join(app.config.get('CONTENT_DIR'), 'config.py'))
except IOError:
	print "Startup Failure: You need to place a config.py in your content directory."

from flask.ext.script import Manager
manager = Manager(app)

from flask.ext.login import LoginManager
loginmanager = LoginManager()
loginmanager.init_app(app)
loginmanager.login_view = 'user_login'

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
	form = CreateForm()
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
		return render_template('search.html', form=form, \
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
