
import os
import re

from werkzeug.local import LocalProxy
import markdown
from flask import g
from flask import current_app
from flask import (Flask, render_template, flash, redirect, url_for, request,
                   abort)

from flask_login import (LoginManager, login_required, current_user,
                             login_user, logout_user)

from .core import Wiki
from .user import UserManager



def get_wiki():
    wiki = getattr(g, '_wiki', None)
    if wiki is None:
        wiki = g._wiki = Wiki(current_app.config['CONTENT_DIR'])
    return wiki

wiki = LocalProxy(get_wiki)

def get_users():
    users = getattr(g, '_users', None)
    if users is None:
        users = g._users = UserManager(current_app.config['CONTENT_DIR'])
    return wiki

users = LocalProxy(get_users)


def create_app():
    app = Flask(__name__)
    app.config['CONTENT_DIR'] = '.'
    app.config['TITLE'] = 'wiki'
    try:
        app.config.from_pyfile(
            os.path.join(app.config.get('CONTENT_DIR'), 'config.py')
        )
    except IOError:
        print ("Startup Failure: You need to place a "
               "config.py in your content directory.")

    loginmanager.init_app(app)

    return app


loginmanager = LoginManager()
loginmanager.login_view = 'user_login'

@loginmanager.user_loader
def load_user(name):
    return users.get_user(name)

