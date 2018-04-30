import logging

from datetime import timedelta
from rq_scheduler import Scheduler as RQScheduler

from .manager import manager


logger = logging.getLogger(__name__)


class Scheduler(object):
    def __init__(self):
        self.register = {}

    @property
    def scheduler(self):
        _scheduler = RQScheduler(
            queue_name=manager.queue.scheduler,
            interval=manager.scheduler_interval,
            connection=manager.connection
        )

        _scheduler.scheduler_key = manager.scheduler.key
        _scheduler.scheduled_jobs_key = manager.scheduler.jobs
        return _scheduler

    @property
    def running(self):
        conn = manager.connection
        key = manager.scheduler.key
        connection_ok = conn.exists(key)
        dead = conn.hexists(key, "death")
        return connection_ok and not dead

    def cancel_job(self, job):
        logger.info(u"canceling %s", job)
        return self.scheduler.cancel(job)

    def cron(self, cron_string, queue, description, timeout):
        def make_cron(func):
            opts = {
                "cron": cron_string, "queue": queue,
                "description": description,
                "timeout": timeout
            }
            self.register[func] = opts
            return func
        return make_cron

    def schedule_in(self, seconds, func, description, args=None, job_id=None):
        args = args or []
        return self.scheduler.enqueue_in(
            timedelta(seconds=seconds),
            func, *args,
            job_ttl=manager.job_ttl,
            job_result_ttl=manager.result_ttl,
            job_description=description,
            job_id=job_id,
            timeout=manager.worker_timeout
        )

    def cancel(self, job_id):
        self.scheduler.cancel(job_id)

    def start_cron_jobs(self):
        if self.running:
            raise ValueError("another scheduler is running")

        for job in self.scheduler.get_jobs():
            if job.meta.get("cron_string"):
                logger.info(u"canceling <Cron %s>", job.func.__name__)
                self.cancel_job(job)

        for func, opts in self.register.items():
            cron = opts.pop("cron")
            queue = opts.pop("queue")
            description = opts.pop("description")
            timeout = opts.pop("timeout")

            logger.info(
                u"add <cron %s[%s]> to @%s",
                func.__name__, cron, queue
            )

            self.scheduler.cron(
                cron_string=cron,
                queue_name=queue,
                func=func, description=description,
                timeout=timeout
            )
        self.scheduler.run(burst=False)
