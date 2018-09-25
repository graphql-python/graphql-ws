#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open("README.rst") as readme_file:
    readme = readme_file.read()

readme = ""

with open("HISTORY.rst") as history_file:
    history = history_file.read()

requirements = [
    "graphql-core>=2.0<3",
    # TODO: put package requirements here
]

setup_requirements = [
    "pytest-runner",
    # TODO(graphql-python): put setup requirements (distutils extensions,
    # etc.) here
]

test_requirements = [
    "pytest",
    # TODO: put package test requirements here
]

setup(
    name="graphql-ws",
    version="0.3.0",
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
    ],
    test_suite="tests",
    tests_require=test_requirements,
    setup_requires=setup_requirements,
)
