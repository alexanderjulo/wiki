import os
from flask import Flask, render_template, flash, redirect, url_for
from flask.ext.wtf import Form, TextField, TextAreaField, Required, \
ValidationError

app = Flask(__name__)
app.config['CONTENT_DIR'] = 'content'
try:
	app.config.from_pyfile(os.path.join(app.config.get('CONTENT_DIR'), 'config.py'))
except IOError:
	print "Startup Failure: You need to place a config.py in your content directory."

from wiki import Wiki
wiki = Wiki(app.config.get('CONTENT_DIR'))

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

@app.route('/')
def home():
	page = wiki.get('home')
	if page:
		return display('home')
	return render_template('home.html')

@app.route('/index/')
def index():
	pages = wiki.index()
	return render_template('index.html', pages=pages)

@app.route('/<path:url>/')
def display(url):
	page = wiki.get_or_404(url)
	return render_template('page.html', page=page)

@app.route('/create/', methods=['GET', 'POST'])
def create():
	form = CreateForm()
	if form.validate_on_submit():
		return redirect(url_for('edit', url=form.url.data))
	return render_template('create.html', form=form)


@app.route('/edit/<path:url>/', methods=['GET', 'POST'])
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
def delete(url):
	page = wiki.get_or_404(url)
	wiki.delete(url)
	flash('Page "%s" was deleted.' % page.title, 'success')
	return redirect(url_for('home'))
	

@app.route('/tags/')
def tags():
	tags = wiki.get_tags()
	return render_template('tags.html', tags=tags)

@app.route('/tag/<string:name>/')
def tag(name):
	tagged = wiki.index_by_tag(name)
	return render_template('tag.html', pages=tagged, tag=name)

@app.route('/search/', methods=['GET', 'POST'])
def search():
	form = SearchForm()
	if form.validate_on_submit():
		results = wiki.search(form.term.data)
		return render_template('search.html', form=form, \
			results=results, search=form.term.data)
	return render_template('search.html', form=form, search=None)

if __name__ == '__main__':
	app.config['DEBUG'] = True
	app.run()