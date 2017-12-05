#!/usr/bin/env python

from setuptools import setup


install_requires = [
    "Flask-Admin>=1.5.0",
    "Flask>=0.12.2",
    "hiredis>=0.2.0",
    "pyroute2>=0.4.20",
    "raven>=6.1.0",
    "redis>=2.10.5",
    "rq-dashboard>=0.3.7",
    "rq-scheduler>=0.7.0",
    "rq>=0.8.0",
    "statsd>=3.2.0"
]


setup(
    name="Flask-RQ",
    version="0.1.0",
    description="Flask RQ",
    url="https://github.com/huangxiaohen2738/flask-rq",
    download_url="https://github.com/huangxiaohen2738/flask-rq",
    author_email="huangxiaohen2738@gmail.com",
    py_modules=["flask_rq"],
    install_requires=install_requires,
    classifiers=[
        "Development Status :: 4 - Beta"
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: BSD License",
        "Topic :: System :: Networking",
        "Topic :: Terminals",
        "Topic :: Utilities"
    ]
)

