import os
from unittest import TestCase
from tempfile import mkdtemp
from tempfile import mkstemp
import shutil

from wiki.core import Wiki

#: the default configuration
CONFIGURATION = u"""
PRIVATE=False
TITLE='test'
DEFAULT_SEARCH_IGNORE_CASE=False
DEFAULT_AUTHENTICATION_METHOD='hash'
"""


class WikiBaseTestCase(TestCase):

    #: The contents of the ``config.py`` file.
    config_content = CONFIGURATION

    _wiki = None

    def setUp(self):
        """
            Creates a content directory for the wiki to use
            and adds a configuration file with some example content.
        """
        self.rootdir = mkdtemp()
        self.create_file(u'config.py', self.config_content)

    @property
    def wiki(self):
        if not self._wiki:
            self._wiki = Wiki(self.rootdir)
        return self._wiki

    def create_file(self, name, content=u'', folder=None):
        """
            Easy way to create a file.

            :param unicode name: the name of the file to create
            :param unicode content: content of the file (optional)
            :param unicode folder: the folder where the file should be
                created, defaults to the temporary directory

            :returns: the absolute path of the newly created file
            :rtype: unicode
        """
        if folder is None:
            folder = self.rootdir

        path = os.path.join(folder, name)
        with open(path, 'w') as fhd:
            fhd.write(content.encode("UTF-8"))

        return path


    def tearDown(self):
        """
            Will remove the root directory and all contents if one
            exists.
        """
        if self.rootdir and os.path.exists(self.rootdir):
            shutil.rmtree(self.rootdir)
