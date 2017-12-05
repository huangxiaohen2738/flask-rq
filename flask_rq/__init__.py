#!/usr/bin/env python
# -*-coding: utf-8-*-

import logging
import os
import random
import rq_dashboard
import socket

from datetime import timedelta
from flask import redirect, url_for
from flask_admin.menu import MenuLink
from flask_security import current_user, login_required
from raven import Client
from redis import StrictRedis, ConnectionPool
from rq import Queue, SimpleWorker, get_current_job
from rq.contrib.legacy import cleanup_ghosts
from rq.contrib.sentry import register_sentry
from rq.job import Job
from rq_scheduler import Scheduler as RQScheduler
from statsd import StatsClient
from pyroute2 import IPDB

logger = logging.getLogger(__name__)
HOSTNAME = socket.gethostname()


def get_redis_conn(config):
    pool = ConnectionPool(
        host=config["REDIS_HOST"],
        port=config["REDIS_PORT"],
        password=config.get("REDIS_PASSWORD"),
        db=config["REDIS_DB"]
    )
    connection = StrictRedis(connection_pool=pool)
    logger.info("connected to {0}".format(connection))
    return connection


class DebugRQConnection(object):
    def enqueue(self, func, *args, **kwargs):
        logger.warn("DEBUG RQ: {0} {1} {2}".format(func, args, kwargs))
        func(*args, **kwargs)

    def enqueue_call(self, func, args=None, kwargs=None, *_args, **_kwargs):
        logger.warn("DEBUG RQ: {0} {1} {2}".format(func, args, kwargs))
        func(*args, **kwargs)


class RQStats(object):
    def __init__(self, namespace):
        self.rate = 0.1
        self.client = None

        self._namespace = namespace
        self._queues = []
        self._connection = None

    def init_app(self, app, queues, connection):
        enabled = app.config.get("RQ_STATSD_ENABLED", True)
        port = app.config.get("RQ_STATSD_PORT", 8125)
        rate = float(app.config.get("RQ_REPORT_RATE", 0.1))
        if 0 <= rate <= 1:
            self.rate = rate

        if not enabled:
            return
        try:
            with IPDB() as ip:
                host = ip.routes.get("default", {})["gateway"]
                self.client = StatsClient(host, port, prefix="rq")
        except Exception as e:
            raise e

        self._queues = [
            Queue(qname, connection=connection)
            for qname in queues
        ]
        self._connection = connection

    def report(self):
        if self.client is None:
            return
        elif random.random() > self.rate:
            return

        count = len(SimpleWorker.all(connection=self._connection))
        reports = [("{0}.workers.count".format(self._namespace), count)]

        for queue in self._queues:
            metric = "{0}.length".format(queue.name.replace(":", "."))
            reports.append((metric, len(queue)))

        for metric, val in reports:
            logger.debug("%s is %d" % (metric, val))
            self.client.gauge(metric, val)


class RQ(object):
    def __init__(self, namespace, scheduler_queue, stats):
        self.DROP = "{0}:drop".format(namespace)
        self.HIGH = "{0}:high".format(namespace)
        queues = list(set([self.DROP, self.HIGH] + scheduler_queue))

        self._debug = None
        self._connection = None

        self._queues = queues
        self._stats = stats

    def init_app(self, app, admin):
        if app.config.get("RQ_DEBUG", False):
            self._debug = DebugRQConnection()

        self._connection = get_redis_conn(app.config)
        self._stats.init_app(app, self.queues, self.connection)

        self.sentry_dsn = app.config.get("SENTRY_DSN")

        self.default_worker_ttl = app.config.get("RQ_DEFAULT_WORKER_TTL", 420)
        self.default_result_ttl = app.config.get("RQ_DEFAULT_RESULT_TTL", 0)
        self.default_timeout = app.config.get("RQ_DEFAULT_TIMEOUT", 180)

        app.config.setdefault("RQ_POLL_INTERVAL", 10 * 1000)

        @rq_dashboard.blueprint.before_request
        @login_required
        def protect_admin_panel():
            if not current_user.has_role("admin"):
                return redirect(url_for("security.login"))

        app.register_blueprint(rq_dashboard.blueprint, url_prefix="/rq")
        admin.add_link(MenuLink("RQ", "/rq"))

    @property
    def queues(self):
        return self._queues[:]

    @property
    def connection(self):
        return self._connection

    def get(self, queue_name):
        if self._debug is not None:
            return self._debug
        if queue_name not in self._queues:
            raise ValueError("invalid queue name: {0}, choose from {1}".format(
                queue_name, self._queues
            ))
        return Queue(
            queue_name,
            connection=self.connection,
            default_timeout=self.default_timeout
        )

    def get_current_job(self):
        return get_current_job(connection=self.connection)

    def enqueue(self, queue_name, fn, *args, **kwargs):
        self._stats.report()
        return self.get(queue_name).enqueue(fn, *args, **kwargs)

    def enqueue_call(self, queue_name, fn, *args, **kwargs):
        self._stats.report()
        return self.get(queue_name).enqueue_call(func=fn, *args, **kwargs)

    def start_worker(self, node=HOSTNAME):
        if self._debug is not None:
            logger.warn("running in debug mode")
            return

        name = "{0}:{1}".format(node, os.getpid())
        q_names = self.queues
        cleanup_ghosts(self.connection)

        exception_handlers = []
        rqs = [Queue(queue, connection=self.connection) for queue in q_names]

        worker = SimpleWorker(
            rqs, name=name, connection=self.connection,
            default_worker_ttl=self.default_worker_ttl,
            default_result_ttl=self.default_result_ttl,
            job_class=Job, queue_class=Queue,
            exception_handlers=exception_handlers or None
        )

        if self.sentry_dsn:
            client = Client(self.sentry_dsn)
            register_sentry(client, worker)

        worker.work(burst=False)


class Scheduler(object):
    def __init__(self, namespace, stats):
        self.scheduler = None
        self._stats = stats
        self.register = {}

        self.RQ_SCHEDULE = "{0}:cron".format(namespace)
        self.SCHEDULER_KEY = "{0}:scheduler".format(namespace)
        self.JOB_KEY = "{0}:scheduler:scheduled_jobs".format(namespace)

    def init_app(self, app):
        scheduler = RQScheduler(
            queue_name=self.RQ_SCHEDULE,
            connection=get_redis_conn(app.config)
        )

        scheduler.scheduler_key = self.SCHEDULER_KEY
        scheduler.scheduled_jobs_key = self.JOB_KEY
        self.scheduler = scheduler

    @property
    def running(self):
        conn = self.scheduler.connection
        connection_ok = conn.exists(self.SCHEDULER_KEY)
        dead = conn.hexists(self.SCHEDULER_KEY, "death")
        return connection_ok and not dead

    def get_jobs(self):
        return self.scheduler.get_jobs()

    def cancel_job(self, job):
        logger.info("canceling {0}".format(job))
        return self.scheduler.cancel(job)

    def start_cron_jobs(self):
        if self.running:
            raise ValueError("another scheduler is running")

        for job in self.get_jobs():
            if job.meta.get("cron_string"):
                logger.info("canceling <Cron {0}>".format(job.func.__name__))
                self.cancel_job(job)

        for func, opts in self.register.items():
            cron = opts.pop("cron")
            queue = opts.pop("queue")
            logger.info("add <cron {0}[{1}]> to @{2}".format(
                func.__name__, cron, queue
            ))
            self.scheduler.cron(cron, func=func, queue_name=queue, **opts)
        self.scheduler.run(burst=False)

    def cron(self, cron, queue, **opts):
        def make_cron(func):
            opts.update({"cron": cron, "queue": queue})
            self.register[func] = opts
            return func
        return make_cron

    def schedule_in(self, seconds, func, *args, **kwargs):
        self._stats.report()
        self.scheduler.enqueue_in(
            timedelta(seconds=seconds),
            func, *args, **kwargs
        )


def create_rq(namespace):
    stats = RQStats(namespace)
    scheduler = Scheduler(namespace, stats)
    rqueue = RQ(namespace, [scheduler.RQ_SCHEDULE], stats)
    return rqueue, scheduler
