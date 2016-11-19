"""
    Wiki core
    ~~~~~~~~~
"""
import os
import re
from collections import OrderedDict

import markdown
from flask import abort


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
        # the markdown meta plugin does not retain the order of the
        # entries, so we have to loop over the meta values a second
        # time to put them into a dictionary in the correct order
        metas, body = self.content.split('\n\n', 1)
        markdown_meta = md.Meta
        meta = OrderedDict()
        for line in metas.split('\n'):
            key = line.split(':', 1)[0]
            # markdown metadata always returns a list of lines, we will reverse
            # that here
            meta[key.lower()] = '\n'.join(markdown_meta[key.lower()])
        return phtml, body, meta


class Page(object):
    def __init__(self, path, url, new=False):
        self.path = path
        self.url = url
        self._meta = OrderedDict()
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
        return self._meta[name]

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
        source = os.path.join(self.root, url) + '.md'
        target = os.path.join(self.root, newurl) + '.md'
        # normalize root path (just in case somebody defined it absolute,
        # having some '../' inside) to correctly compare it to the target
        root = os.path.normpath(self.root)
        # get root path longest common prefix with normalized target path
        common = os.path.commonprefix((root, os.path.normpath(target)))
        # common prefix length must be at least as root length is
        # otherwise there are probably some '..' links in target path leading
        # us outside defined root directory
        if len(common) < len(root):
            raise RuntimeError(
                'Possible write attempt outside content directory: '
                '%s' % newurl)
        # create folder if it does not exists yet
        folder = os.path.dirname(target)
        if not os.path.exists(folder):
            os.makedirs(folder)
        os.rename(source, target)

    def delete(self, url):
        path = self.path(url)
        if not self.exists(url):
            return False
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
