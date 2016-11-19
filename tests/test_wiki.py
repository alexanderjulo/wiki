from . import WikiBaseTestCase


class WikiTestCase(WikiBaseTestCase):

    def test_simple_file_detection(self):
        self.create_file('test.md')
        assert self.wiki.exists('test') is True

    def test_wrong_extension_detection(self):
        self.create_file('test.txt')
        assert self.wiki.exists('test') is False

    def test_config_is_unreadable(self):
        # the config file is automatically created, so we can just run
        # tests without having to worry about anything
        assert self.wiki.exists('config') is False
        assert self.wiki.exists('config.py') is False
