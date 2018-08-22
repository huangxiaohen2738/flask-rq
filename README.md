[![Build Status](https://travis-ci.org/huangxiaohen2738/flask-rq.svg?branch=master)](https://travis-ci.org/huangxiaohen2738/flask-rq)

# Flask-RQ
flask-rq


## How to Use
#### Create

```python
from flask_rq import create_rq

manager, rqueue, scheduler = create_rq("some-name-space")
```

#### Init

```python
admin = Admin(app)
manager.init_app(app)
manager.init_admin(app, admin) # if you want
```

#### Enqueue

```python
rqueue.enqueue(manager.queue.high, some_func, "description")

@scheduler.cron("*/5 * * * *", manager.queue.cron) 
def every_5_min():
    print("runs every 5min!")

scheduler.schedule_in(10, test_func, "description", args=(1, 2))

```

#### Run

```python
rqueue.start_worker()

# by start cron jobs, all previous cron jobs will be canceled
scheduler.start_cron_jobs()
```


#### Config
```python
RQ_HOST = "localhost"
RQ_PORT = 6379
RQ_PASSWORD = "password"
RQ_DB = 0
RQ_DEBUG = False
SENTRY_DSN = ""
# report status(need stastd); If you don't want to use it, set False
RQ_STATSD_ENABLED = True  
RQ_WORKER_TTL = 420
RQ_RESULT_TTL = 0
RQ_WORKER_TIMEOUT = 180
```
