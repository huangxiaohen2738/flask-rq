# -*- coding: utf8 -*-

from flask import redirect, url_for
from flask_admin.menu import MenuLink
from flask_security import current_user, login_required
from rq import pop_connection, push_connection
from rq_dashboard import blueprint


class FakeState(object):
    first_registration = False

    def __init__(self, blueprint):
        self.blueprint = blueprint

    def add_url_rule(self, rule, endpoint, view_func, **options):
        self.blueprint.add_url_rule(rule, endpoint, view_func, **options)

    def route_only(self):
        registered = self.blueprint.deferred_functions
        self.blueprint.deferred_functions = []
        for func in registered:
            func(self)


class Dashboard(object):
    def init(self, app, admin, connection):
        fstate = FakeState(blueprint)
        fstate.route_only()

        @blueprint.before_request
        @login_required
        def protect_admin_panel():
            if not current_user.has_role("admin"):
                return redirect(url_for("security.login"))
            push_connection(connection)

        @blueprint.teardown_request
        def pop_rq_connection(exception=None):
            pop_connection()

        @blueprint.context_processor
        def inject_interval():
            return dict(poll_interval=5 * 1000)

        app.register_blueprint(blueprint, url_prefix="/rq")
        admin.add_link(MenuLink("RQ", "/rq"))


dashboard = Dashboard()
