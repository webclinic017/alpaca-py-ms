#!/usr/bin/env python

import ast
import os
import re
from setuptools import setup

_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open('alpaca/__init__.py', 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))

with open('README.md') as readme_file:
    README = readme_file.read()

with open(os.path.join("requirements", "requirements.txt")) as reqs:
    REQUIREMENTS = reqs.readlines()

with open(os.path.join("requirements", "requirements_test.txt")) as reqs:
    REQUIREMENTS_TEST = reqs.readlines()


setup(
    name='alpaca-py-ms',
    version=version,
    description='Alpaca Python API microservice',
    long_description=README,
    long_description_content_type='text/markdown',
    author='Jeff Aggas',
    author_email='jeffrey.aggas@gmail.com',
    url='https://github.com/jaggas/alpaca-py-ms',
    keywords='financial,timeseries,api,trade',
    packages=[
        'alpaca-py-ms',
    ],
    install_requires=REQUIREMENTS,
    tests_require=REQUIREMENTS_TEST,
    setup_requires=['pytest-runner', 'flake8'],
)
