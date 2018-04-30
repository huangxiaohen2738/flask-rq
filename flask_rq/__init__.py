from .manager import manager
from .scheduler import Scheduler
from .worker import RQ


def create_rq(namespace):
    manager.set_namespace(namespace)

    scheduler = Scheduler()
    rqueue = RQ()

    return manager, rqueue, scheduler
