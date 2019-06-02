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
    # toDO: switch to core-next
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
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.6",
    ],
    test_suite="tests",
    tests_require=test_requirements,
    setup_requires=setup_requirements,
)
