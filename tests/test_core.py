# -*- coding: utf-8 -*-
from wiki.core import Page

from . import WikiBaseTestCase


PAGE_CONTENT = u"""\
title: Test
tags: one, two, 3, jö

Hello, how are you guys?

**Is it not _magnificent_**?
"""


class PageTestCase(WikiBaseTestCase):


    page_content = PAGE_CONTENT

    def setUp(self):
        super(PageTestCase, self).setUp()

        self.page_path = self.create_file('test.md', self.page_content)
        self.page = Page(self.page_path, 'test')

    def test_page_loading(self):
        assert self.page.content == PAGE_CONTENT

    def test_page_meta(self):
        assert self.page.title == u'Test'
        assert self.page.tags == u'one, two, 3, jö'

    def test_page_saving(self):
        self.page.save()
        with open(self.page_path, 'rU') as fhd:
            saved = fhd.read().decode("UTF-8")
        assert saved == self.page_content


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
