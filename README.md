# Readme

## About
As I wanted a wiki that just uses plain files as backend, that is easy
to use and that is written in python, to enable me to easily hack around,
but found nothing, I just wrote this down. I hope that it might help others ,too.

## Features

* Markdown (default) or reStructuredText Syntax Editing
* Tags
* Regex Search
* Random URLs
* Web Editor
* Pages can also be edited manually, possible uses are:
	* use the cli
	* use your favorite editor
	* sync with dropbox
	* and many more
* easily themable

### Planned

* Speed Improvements
	* Code Optimizations
	* Caching
* Wikilinks-Support
* Access protection (for private wikis or to limit edits to a known group)
* Settings via the webinterface


## Setup
Just clone this repository, cd into it, run `pip install -r requirements.txt`
and create `content/` in the root directory with a `config.py` in it,
that contains at least the following:

	# encoding: <your encoding (probably utf-8)
	SECRET_KEY='a unique and long key'
	TITLE='Wiki' # Title Optional

If you want to use reStructuredText instead of Markdown, install `docutils` and add 
        
        MARKUP='restructuredtext' 

to the config file. 

## Start
Afterwards just run the app however you want. I personally recommend something
like gunicorn:
	
	gunicorn app:app

You can install `setproctitle` with pip to get meaningful process names.

If you just want to try something out or debug something, you can execute
the app with `python app.py` which will run the development server in debug
mode. Have fun.

## Theming
The templates are based on jinja2. I used
[bootstrap](http://twitter.github.com/bootstrap/) for the design.
If you want to change the overall design, you should edit `templates/base.html`
and/or `static/bootstrap.css`. If you do not like specific parts of the site,
it should be fairly easy to find the equivalent template and edit it.

## Contributors

Thank you very much to my two top contributers @walkerh and @traeblain. You two have posted so many issues and especially solved them with so many pull requests, that I sometimes lose track of it! :)
