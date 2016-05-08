import os
import unittest
import tempfile
import shutil

# TODO default content dir must exists before import
import app


def write_dummy_config(path):
    cfg = os.path.join(path, 'config.py')
    with open(cfg, 'w') as f:
        f.write("SECRET_KEY='testing'")
        f.flush()
        os.fsync(f.fileno())


class PublicAppTest(unittest.TestCase):
    def setUp(self):
        self.tmp_content = tempfile.mkdtemp()
        app.app.config['CONTENT_DIR'] = self.tmp_content
        app.app.config['PRIVATE'] = False
        # app global variables must be reconfigured to new content dir
        app.wiki = app.Wiki(self.tmp_content)
        app.users = app.UserManager(self.tmp_content)
        # create config.py in testing content dir
        write_dummy_config(self.tmp_content)
        self.app = app.app.test_client()

    def tearDown(self):
        shutil.rmtree(self.tmp_content)

    def test_home(self):
        res = self.app.get('/')
        self.assertTrue('Welcome to your new wiki' in res.data)


class UserManagerTest(unittest.TestCase):
    def setUp(self):
        self.path = tempfile.mkdtemp()
        self.manager = app.UserManager(self.path)
        # Unfortunately app.UserManager has decorators for locking, which
        # closes inside itself path to the lock file known at definition time.
        # This means default content dir lock file is being used even if app
        # is reconfigured later. Currently I do not know nice & easy solution.

    def tearDown(self):
        shutil.rmtree(self.path)

    def test_adding(self):
        self.manager.add_user('user', 'pass')
        # try to read new users data
        user = self.manager.get_user('user')
        self.assertTrue(user)
        self.assertEqual('user', user.get_id())
        # try to find non existing user
        user = self.manager.get_user('noUser')
        self.assertFalse(user)


if __name__ == '__main__':
    unittest.main()