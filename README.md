# Readme

[![Linux build status](https://travis-ci.org/alexanderjulo/wiki.svg?branch=master)](https://travis-ci.org/alexanderjulo/wiki)
[![Windows build status](https://ci.appveyor.com/api/projects/status/n4gh7bbf93fiixew/branch/master?svg=true)](https://ci.appveyor.com/project/alexanderjulo/wiki/branch/master)
[![Join the chat at https://gitter.im/gitterHQ/gitterHQ.github.io](https://badges.gitter.im/gitterHQ/gitterHQ.github.io.svg)](https://gitter.im/wiki/Lobby?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

## About
As I wanted a wiki that just uses plain markdown files as backend, that is easy
to use and that is written in python, to enable me to easily hack around,
but found nothing, I just wrote this down. I hope that it might help others ,too.

## Features

* Markdown Syntax Editing
* Tags
* Regex Search
* Random URLs
* Web Editor
* Pages can also be edited manually, possible uses are:
	* use the cli
	* use your favorite editor
	* sync with dropbox
	* and many more

### Planned

* Re-introduce support for customizing the theme
* Speed Improvements
	* Code Optimizations
	* Caching
* Settings via the webinterface
* Python2 & 3 compatibility.


## Setup
You can install wiki using:

	pip install wiki2


Afterwards you can create or change into your content directory and create a `config.py` file in it, that contains at least the following:

	# encoding: <your encoding (probably utf-8)
	SECRET_KEY='a unique and long key'
	TITLE='Wiki' # Title Optional

## Usage
Afterwards you can just run `wiki web` in your content directory to start the server.

## Development
If you plan on helping with the development of this project you can clone the repository, open the newly created directory in a terminal and run `pip install -e .`, after which both the tests and the wiki cli will be available to you.

## Contributors

Thank you very much to my two top contributers @walkerh and @traeblain. You two have posted so many issues and especially solved them with so many pull requests, that I sometimes lose track of it! :)
