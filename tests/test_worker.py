def test_config(app):
    config = dict(
        RQ_HOST="localhost",
        RQ_PORT=6379,
        RQ_PASSWORD="password",
        RQ_DB=0,
        RQ_DEBUG=False,
        SENTRY_DSN="",
        RQ_STATSD_ENABLED=False,
        RQ_RESULT_TTL=0,
        RQ_WORKER_TIMEOUT=180,
    )
    app.config.update(config)
    assert app.config["RQ_HOST"] == "localhost"


def test_init(app, admin):
    from flask_rq import create_rq

    manager, rqueue, scheduler = create_rq("test")
    manager.init_app(app)
