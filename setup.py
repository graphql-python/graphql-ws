#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import find_packages, setup

with open("README.rst") as readme_file:
    readme = readme_file.read()

readme = ""

with open("HISTORY.rst") as history_file:
    history = history_file.read()

requirements = [
    "graphql-core>=3.0.0",
    # TODO: put package requirements here
]

setup_requirements = [
    "pytest-runner",
    # TODO(graphql-python): put setup requirements (distutils extensions,
    # etc.) here
]

test_requirements = [
    "pytest",
    "pytest-aiohttp",
    'asyncmock; python_version<"3.8"',
]

setup(
    name="graphql-ws",
    version="0.3.1",
    description="Websocket server for GraphQL subscriptions",
    long_description=readme + "\n\n" + history,
    author="Syrus Akbary",
    author_email="me@syrusakbary.com",
    url="https://github.com/graphql-python/graphql-ws",
    packages=find_packages(include=["graphql_ws"]),
    include_package_data=True,
    install_requires=requirements,
    license="MIT license",
    zip_safe=False,
    keywords=["graphql", "subscriptions", "graphene", "websockets"],
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    test_suite="tests",
    tests_require=test_requirements,
    setup_requires=setup_requirements,
)
