import logging
import uuid

from raven import Client
from rq import Queue
from rq.contrib.legacy import cleanup_ghosts
from rq.contrib.sentry import register_sentry
from rq.job import Job

from .manager import manager
from .constants import HOSTNAME
from .debug import DebugRQConnection
from .worker import FlaskWorker


logger = logging.getLogger(__name__)


class RQ(object):
    def __init__(self):
        self._queue = None

    @property
    def queues(self):
        if self._queue is None:
            self._queue = list(set(manager.queue._asdict().values()))
        return self._queue

    def get(self, queue_name):
        if manager.debug:
            return DebugRQConnection()
        if queue_name not in self.queues:
            raise ValueError("invalid queue name: {0}, choose from {1}".format(
                queue_name, self.queues
            ))
        return Queue(
            queue_name,
            connection=manager.connection,
            default_timeout=manager.worker_timeout
        )

    def enqueue(self, queue_name, fn, description, args=None, kwargs=None):
        queue = self.get(queue_name)
        return queue.enqueue_call(
            func=fn, args=args, kwargs=kwargs,
            description=description,
            timeout=manager.worker_timeout,
            ttl=manager.job_ttl,
            result_ttl=manager.result_ttl
        )

    def start_worker(self, node=HOSTNAME, logging_level="INFO"):
        if manager.debug:
            logger.warn("running in debug mode")
            return

        name = "{0}:{1}".format(node, uuid.uuid4().hex[:8])
        q_names = self.queues
        cleanup_ghosts(manager.connection)

        rqs = [
            Queue(queue, connection=manager.connection)
            for queue in q_names
        ]

        worker = FlaskWorker(
            rqs, name=name, connection=manager.connection,
            default_worker_ttl=manager.worker_ttl,
            default_result_ttl=manager.result_ttl,
            job_class=Job, queue_class=Queue,
            exception_handlers=None,
        )

        if manager.sentry_dsn:
            client = Client(manager.sentry_dsn)
            register_sentry(client, worker)

        worker.work(burst=False, logging_level=logging_level)
