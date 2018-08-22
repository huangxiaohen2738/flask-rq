import logging
import time

from rq import SimpleWorker

from .manager import manager
from .constants import HOSTNAME


logger = logging.getLogger(__name__)


class FLaskWorker(SimpleWorker):
    def timing(self, name, value):
        manager.stats.timing(name, value)

    def execute_job(self, job, *args, **kwargs):
        start = time.time()
        key = "job.{0}".format(job.func_name)

        manager.stats.incr("{0}.count".format(key))

        self.perform_job(job, *args, **kwargs)
        ms = int((time.time() - start) * 1000)

        status = job.get_status() or "unknown"
        logger.info(
            u"%s@%s status (%s) after %dms",
            key, HOSTNAME, status, ms
        )
        manager.stats.timing("{0}.{1}".format(key, status), ms)
