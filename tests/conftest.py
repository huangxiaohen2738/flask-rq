#!/usr/bin/env python
# -*-coding: utf-8-*-

import pytest
from flask import Flask


@pytest.fixture(scope="session")
def app():
    app = Flask(__name__)
    return app


@pytest.fixture(scope="session")
def admin():
    from flask_admin import Admin
    admin = Admin()
    return admin
