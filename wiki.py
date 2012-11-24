import os
import re
import markdown
from flask import abort

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
		md = markdown.Markdown(['codehilite', 'meta'])
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
