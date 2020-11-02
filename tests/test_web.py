from . import WikiBaseTestCase


CONFIGURATION_PRIVATE = u"""
PRIVATE=True
TITLE='test'
DEFAULT_SEARCH_IGNORE_CASE=False
DEFAULT_AUTHENTICATION_METHOD='hash'
SECRET_KEY='test'
"""


class WebContentTestCase(WikiBaseTestCase):
    """
        Various test cases around web content.
    """

    def test_index_missing(self):
        """
            Assert the wiki will correctly play the content missing
            index page, if no index page exists.
        """
        rsp = self.app.get('/')
        assert b"You did not create any content yet." in rsp.data
        assert rsp.status_code == 200


class AuthenticationTestCase(WikiBaseTestCase):
    """
        Test cases around authentication.
    """

    config_content = CONFIGURATION_PRIVATE

    def test_auth_protection_works(self):
        """
            Assert that if auth is required and user is not
            authenticated the request fails.
        """
        rsp = self.app.get('/')
        assert rsp.status_code == 302
        assert rsp.headers['Location'] == "http://localhost/user/login/?next=%2F"
