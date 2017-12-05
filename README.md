[![Build Status](https://travis-ci.org/huangxiaohen2738/flask-rq.svg?branch=master)](https://travis-ci.org/huangxiaohen2738/flask-rq)
[![Coverage Status](https://coveralls.io/repos/github/huangxiaohen2738/flask-rq/badge.svg)](https://coveralls.io/github/huangxiaohen2738/flask-rq)

# Flask-RQ
flask-rq


## How to Use
#### Create

```python
from lyqr import create_rq

rqueue, scheduler = create_rq("some-name-space")
```

#### Init

```python
rqueue.init_app(app, admin)
scheduler.init_app(app)
```

#### Enqueue

```python
rqueuq.enqueue(rqueuq.HIGH, some_func)

@scheduler.cron("*/5 * * * *", rqueue.DROP)
def every_5_min():
    print("runs every 5min!")
```

#### Run

```python
rqueue.start_worker()

# by start cron jobs, all previous cron jobs will be canceled
scheduler.start_cron_jobs()
```


#### Config
```
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_PASSWORD = "password"
REDIS_DB = 0
RQ_DEBUG = False
SENTRY_DSN = ""
RQ_STATSD_ENABLED = True  // report status(need stastd); If you don't want to use it, set False
RQ_STATSD_PORT = 8125
RQ_REPORT_RATE = 0.1
RQ_DEFAULT_WORKER_TTL = 420
RQ_DEFAULT_RESULT_TTL = 0
RQ_DEFAULT_TIMEOUT = 180
RQ_POLL_INTERVAL = 10000
```
