from wiki.web import create_app
from wiki.web.user import UserManager

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
        assert rsp.headers['Location'] == "/user/login/?next=%2F"

    def test_user_can_log_in_and_out(self):
        app = create_app(self.rootdir)
        app.config['WTF_CSRF_ENABLED'] = False
        with app.app_context():
            user = UserManager(self.rootdir).add_user('alice', 'secret')
            assert user.is_active is True
            assert user.is_authenticated is False

        client = app.test_client()
        rsp = client.post(
            '/user/login/',
            data={'name': 'alice', 'password': 'secret'},
        )
        assert rsp.status_code == 302
        assert rsp.headers['Location'] == '/index/'
        assert client.get('/').status_code == 200

        rsp = client.get('/user/logout/')
        assert rsp.status_code == 302
        assert client.get('/').status_code == 302
