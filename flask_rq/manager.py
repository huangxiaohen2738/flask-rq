import logging

from collections import namedtuple
from redis import StrictRedis, ConnectionPool
from statsd import StatsClient
from rq import SimpleWorker
from rq.queue import get_failed_queue

from .dashboard import dashboard
from .constants import GATEWAY


logger = logging.getLogger(__name__)


QUEUE = namedtuple("QUEUE", ["scheduler", "high", "drop"])
SCHEDULER = namedtuple("SCHEDULER", ["key", "jobs"])


class RQManager(object):
    def __init__(self):
        self.queue = QUEUE(None, None, None)
        self.scheduler = SCHEDULER(None, None)

        self._connection = None
        self._scheduler_interval = None
        self._job_ttl = None
        self._result_ttl = None
        self._worker_timeout = None
        self._worker_ttl = None
        self._debug = False
        self._sentry_dsn = None

        self._stats = None

    def set_namespace(self, namesapce):
        namesapce = namesapce.lower()
        self.queue = QUEUE(
            high="{0}:high".format(namesapce),
            drop="{0}:drop".format(namesapce),
            scheduler="{0}:cron".format(namesapce),
        )
        self.scheduler = SCHEDULER(
            key="{0}:scheduler".format(namesapce),
            jobs="{0}:scheduler:scheduled_jobs".format(namesapce)
        )

        prefix = "rq.{0}".format(namesapce)
        self._stats = StatsClient(GATEWAY, 8125, prefix=prefix)

    def init_app(self, app):
        pool = ConnectionPool(
            host=app.config["LYRQ_HOST"],
            port=app.config.get("LYRQ_PORT", 6379),
            password=app.config.get("LYRQ_PASSWORD"),
            db=app.config.get("LYRQ_DB", 0)
        )
        connection = StrictRedis(connection_pool=pool)
        logger.info("connected to {0}".format(connection))
        self._connection = connection
        self._sentry_dsn = app.config.get("SENTRY_DSN")

        self._debug = app.config.get("LYRQ_DEBUG", False)
        self._scheduler_interval = app.config.get("LYRQ_SCHEDULER_INTERVAL")
        self._job_ttl = app.config.get("LYRQ_JOB_TTL")
        self._result_ttl = app.config.get("LYRQ_RESULT_TTL")
        self._worker_ttl = app.config.get("LYRQ_WORKER_TTL")
        self._worker_timeout = app.config["LYRQ_WORKER_TIMEOUT"]

    def init_admin(self, app, admin):
        dashboard.init(app, admin, self.connection)

    @property
    def stats(self):
        return self._stats

    @property
    def debug(self):
        return self._debug

    @property
    def sentry_dsn(self):
        return self._sentry_dsn

    @property
    def connection(self):
        return self._connection

    @property
    def scheduler_interval(self):
        """default scheduler_interval is 30
        """
        return self._scheduler_interval or 30

    @property
    def worker_timeout(self):
        """default worker timeout is 300s
        """
        return self._worker_timeout or 300

    @property
    def job_ttl(self):
        """default job ttl is 30min
        """
        return self._job_ttl or 30 * 60

    @property
    def result_ttl(self):
        """default result ttl is 0s
        """
        return self._result_ttl or 0

    @property
    def worker_ttl(self):
        """default worker ttl is 5min
        """
        return self._worker_ttl or 300

    def get_report_metrics(self):
        conn = self.connection
        worker_count = len(SimpleWorker.all(connection=conn))
        fq = get_failed_queue(connection=conn)
        return {
            "queue.failed": len(fq),
            "queue.workers": worker_count
        }

    def get_queue_metrics(self, rqueue):
        if rqueue is None:
            return {}
        return {
            "queue.{0}".format(queue): len(rqueue.get(queue))
            for queue in rqueue.queues
        }

    def get_scheduler_metrics(self, scheduler):
        if scheduler is None:
            return {}
        return {
            "queue.repeated": len(scheduler.register),
            "queue.scheduled": scheduler.scheduler.count()
        }

    def collect(self, rqueue, scheduler):
        metrics = {}
        metrics.update(self.get_report_metrics())
        metrics.update(self.get_queue_metrics(rqueue))
        metrics.update(self.get_scheduler_metrics(scheduler))

        for name, val in metrics.items():
            logger.info("%s is %d" % (name, val))
            self.stats.gauge(name, val)


manager = RQManager()
