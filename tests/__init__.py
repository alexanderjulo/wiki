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

    def setUp(self):
        """
            Creates a content directory for the wiki to use
            and adds a configuration file with some example content.

            Following that it will create a wiki instance as
            ``self.wiki`` using the created directory.
        """
        self.rootdir = mkdtemp()
        self.create_file(u'config.py', self.config_content)
        self.wiki = Wiki(self.rootdir)

    def create_file(self, name, content=u'', folder=None):
        """
            Easy way to create a file.

            :param str name: the name of the file to create
            :param str content: content of the file (optional)
            :param str folder: the folder where the file should be
                created, defaults to the temporary directory
        """
        if folder is None:
            folder = self.rootdir

        with open(os.path.join(folder, name), 'w') as fhd:
            fhd.write(content)


    def tearDown(self):
        """
            Will remove the root directory and all contents if one
            exists.
        """
        if self.rootdir and os.path.exists(self.rootdir):
            shutil.rmtree(self.rootdir)
