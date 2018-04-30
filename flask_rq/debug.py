import logging

logger = logging.getLogger(__name__)


class DebugRQConnection(object):
    def enqueue(self, func, *args, **kwargs):
        logger.warn(u"DEBUG RQ: %s %s %s", func, args, kwargs)
        func(*args, **kwargs)

    def enqueue_call(self, func, args=None, kwargs=None, *_args, **_kwargs):
        logger.warn(u"DEBUG RQ: %s %s %s", func, args, kwargs)
        func(*args, **kwargs)
