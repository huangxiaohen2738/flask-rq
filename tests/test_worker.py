#!/usr/bin/env python
# -*-coding: utf-8-*-

def test_config(app):
    config = dict( 
        REDIS_HOST = "localhost",
        REDIS_PORT = 6379,
        REDIS_PASSWORD = "password",
        REDIS_DB = 0,
        RQ_DEBUG = False,
        SENTRY_DSN = "",
        RQ_STATSD_ENABLED = False, 
        RQ_STATSD_PORT = 8125,
        RQ_REPORT_RATE = 0.1,
        RQ_DEFAULT_WORKER_TTL = 420,
        RQ_DEFAULT_RESULT_TTL = 0,
        RQ_DEFAULT_TIMEOUT = 180,
        RQ_POLL_INTERVAL = 10000
    )
    app.config.update(config)
    assert app.config["REDIS_HOST"] == "localhost"


def test_init(app, admin):
    from flask_rq import create_rq

    _, rqueue, scheduler = create_rq("test")

    scheduler.init_app(app)
    rqueue.init_app(app, admin)
