import os
from functools import wraps
from flask import Flask, render_template, flash, redirect, url_for, request
from flask.ext.wtf import Form, TextField, TextAreaField, PasswordField, \
Required, ValidationError
from flask.ext.login import LoginManager, current_user, login_user, \
logout_user, login_required


app = Flask(__name__)
app.config['CONTENT_DIR'] = 'content'
try:
	app.config.from_pyfile(os.path.join(app.config.get('CONTENT_DIR'), 'config.py'))
except IOError:
	print "Startup Failure: You need to place a config.py in your content directory."

from flask.ext.script import Manager
manager = Manager(app)

loginmanager = LoginManager()
loginmanager.init_app(app)
loginmanager.login_view = 'login'

from wiki import Wiki
wiki = Wiki(app.config.get('CONTENT_DIR'))

from user import UserManager
users = UserManager(app.config.get('CONTENT_DIR'))

def protect(f):
	@wraps(f)
	def wrapper(*args, **kwargs):
		if app.config.get('PRIVATE') and not current_user.is_authenticated():
			return loginmanager.unauthorized()
		return f(*args, **kwargs)
	return wrapper

@loginmanager.user_loader
def load_user(name):
	return users.get_user(name)

class CreateForm(Form):
	url = TextField('', [Required()])

	def validate_url(form, field):
		if wiki.exists(field.data):
			raise ValidationError('The URL "%s" exists already.' % field.data)

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
		return redirect(url_for('edit', url=form.url.data))
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

@app.route('/login/', methods=['GET', 'POST'])
def login():
	form = LoginForm()
	if form.validate_on_submit():
		user = users.get_user(form.name.data)
		login_user(user)
		user.set('authenticated', True)
		flash('Login successful.', 'success')
		return redirect(request.args.get("next") or url_for('index'))
	return render_template('login.html', form=form)

@app.route('/logout/')
@login_required
def logout():
	current_user.set('authenticated', False)
	logout_user()
	flash('Logout successful.', 'success')
	return redirect(url_for('index'))

if __name__ == '__main__':
	manager.run()