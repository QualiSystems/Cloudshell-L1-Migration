#!/usr/bin/env python
# -*- coding: utf-8 -*-
try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup, find_packages


def get_file_content(file_name):
    with open(file_name) as f:
        return f.read().strip()

setup(
    name='cloudshell-l1-migration',
    version=get_file_content('version.txt'),
    description='QualiSystems CloudShell L1 migration script',
    author='QualiSystems',
    author_email='info@qualisystems.com',
    url='https://github.com/QualiSystems/Cloudshell-L1-Migration',
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    package_data={'migration': ['data/*.yml', 'data/*.json']},
    entry_points={
        "console_scripts": ['migration_tool = cloudshell.layer_one.migration_tool.bootstrap:cli']
    },
    include_package_data=True,
    install_requires=get_file_content('requirements.txt'),
    license="Apache Software License 2.0",
    zip_safe=False,
    keywords='migration cloudshell quali command-line cli',
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python :: 2.7",
        "Topic :: Software Development :: Libraries",
        "License :: OSI Approved :: Apache Software License",
    ],
    test_suite='tests',
    tests_require=get_file_content('test_requirements.txt')
)