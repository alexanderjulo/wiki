from setuptools import setup, find_packages


print(find_packages())

setup(
    name='wiki2',
    version='2.0.3',
    description='simple python markdown wiki with web ui',
    author='Alexander Jung-Loddenkemper',
    author_email='alexander@julo.ch',
    url='https://github.com/alexanderjulo/wiki',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Flask>=0.9',
        'Click>=6,<7',
        'Flask-Login>=0.4',
        'Flask-WTF>=0.8',
        'Markdown>=2.2.0',
        'Pygments>=1.5',
        'WTForms>=1.0.2',
        'Werkzeug>=0.8.3'
    ],
    setup_requires=['pytest-runner'],
    tests_require=['pytest', 'mock'],
    entry_points={
        'console_scripts': [
            'wiki=wiki.cli:main'
        ]
    }
)
