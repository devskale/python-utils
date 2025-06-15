  arq — arq v0.26.3 documentation     

arq[¶](#arq "Permalink to this heading")
========================================

[![pypi](https://img.shields.io/pypi/v/arq.svg)](https://pypi.python.org/pypi/arq) [![license](https://img.shields.io/pypi/l/arq.svg)](https://github.com/samuelcolvin/arq)

Current Version: v0.26.3

Job queues and RPC in python with asyncio and redis.

_arq_ was conceived as a simple, modern and performant successor to [rq](http://python-rq.org/).

Warning

In `v0.16` _arq_ was **COMPLETELY REWRITTEN** to use an entirely different approach to registering workers, enqueueing jobs and processing jobs. You will need to either keep using `v0.15` or entirely rewrite your _arq_ integration to use `v0.16`.

See [here](/old/) for old docs.

Why use _arq_?

**non-blocking**

_arq_ is built using python 3’s [asyncio](https://docs.python.org/3/library/asyncio.html) allowing non-blocking job enqueuing and execution. Multiple jobs (potentially hundreds) can be run simultaneously using a pool of _asyncio_ `Tasks`.

**powerful-features**

Deferred execution, easy retrying of jobs, and pessimistic execution ([see below](#usage)) means _arq_ is great for critical jobs that **must** be completed.

**fast**

Asyncio and no forking make _arq_ around 7x faster than _rq_ for short jobs with no io. With io that might increase to around 40x faster. (TODO)

**elegant**

I’m a long time contributor to and user of [rq](http://python-rq.org/), _arq_ is designed to be simpler, clearer and more powerful.

**small**

and easy to reason with - currently _arq_ is only about 700 lines, that won’t change significantly.

Install[¶](#install "Permalink to this heading")
------------------------------------------------

Just:

pip install arq

Redesigned to be less elegant?[¶](#redesigned-to-be-less-elegant "Permalink to this heading")
---------------------------------------------------------------------------------------------

The approach used in _arq_ `v0.16` of enqueueing jobs by name rather than “just calling a function” and knowing it will be called on the worker (as used in _arq_ `<= v0.15`, rq, celery et al.) might seem less elegant, but it’s for good reason.

This approach means your frontend (calling the worker) doesn’t need access to the worker code, meaning better code separation and possibly smaller images etc.

Usage[¶](#usage "Permalink to this heading")
--------------------------------------------

Warning

**Jobs may be called more than once!**

_arq_ v0.16 has what I’m calling “pessimistic execution”: jobs aren’t removed from the queue until they’ve either succeeded or failed. If the worker shuts down, the job will be cancelled immediately and will remain in the queue to be run again when the worker starts up again (or run by another worker which is still running).

(This differs from other similar libraries like _arq_ `<= v0.15`, rq, celery et al. where jobs generally don’t get rerun when a worker shuts down. This in turn requires complex logic to try and let jobs finish before shutting down (I wrote the `HerokuWorker` for rq), however this never really works unless either: all jobs take less than 6 seconds or your worker never shuts down when a job is running (impossible).)

All _arq_ jobs should therefore be designed to cope with being called repeatedly if they’re cancelled, eg. use database transactions, idempotency keys or redis to mark when an API request or similar has succeeded to avoid making it twice.

**In summary:** sometimes _exactly once_ can be hard or impossible, _arq_ favours multiple times over zero times.

### Simple Usage[¶](#simple-usage "Permalink to this heading")

import asyncio
from httpx import AsyncClient
from arq import create\_pool
from arq.connections import RedisSettings

\# Here you can configure the Redis connection.
\# The default is to connect to localhost:6379, no password.
REDIS\_SETTINGS \= RedisSettings()

async def download\_content(ctx, url):
    session: AsyncClient \= ctx\['session'\]
    response \= await session.get(url)
    print(f'{url}: {response.text:.80}...')
    return len(response.text)

async def startup(ctx):
    ctx\['session'\] \= AsyncClient()

async def shutdown(ctx):
    await ctx\['session'\].aclose()

async def main():
    redis \= await create\_pool(REDIS\_SETTINGS)
    for url in ('https://facebook.com', 'https://microsoft.com', 'https://github.com'):
        await redis.enqueue\_job('download\_content', url)

\# WorkerSettings defines the settings to use when creating the work,
\# It's used by the arq CLI.
\# redis\_settings might be omitted here if using the default settings
\# For a list of all available settings, see https://arq-docs.helpmanual.io/#arq.worker.Worker
class WorkerSettings:
    functions \= \[download\_content\]
    on\_startup \= startup
    on\_shutdown \= shutdown
    redis\_settings \= REDIS\_SETTINGS

if \_\_name\_\_ \== '\_\_main\_\_':
    asyncio.run(main())

(This script is complete, it should run “as is” both to enqueue jobs and run them)

To enqueue the jobs, simply run the script:

python demo.py

To execute the jobs, either after running `demo.py` or before/during:

arq demo.WorkerSettings

Append `--burst` to stop the worker once all jobs have finished. See [`arq.worker.Worker`](#arq.worker.Worker "arq.worker.Worker") for more available properties of `WorkerSettings`.

You can also watch for changes and reload the worker when the source changes:

arq demo.WorkerSettings \--watch path/to/src

This requires [watchfiles](https://pypi.org/project/watchfiles/) to be installed (`pip install watchfiles`).

For details on the _arq_ CLI:

arq \--help

### Startup & Shutdown coroutines[¶](#startup-shutdown-coroutines "Permalink to this heading")

The `on_startup` and `on_shutdown` coroutines are provided as a convenient way to run logic as the worker starts and finishes, see [`arq.worker.Worker`](#arq.worker.Worker "arq.worker.Worker").

For example, in the above example `session` is created once when the work starts up and is then used in subsequent jobs.

### Deferring Jobs[¶](#deferring-jobs "Permalink to this heading")

By default, when a job is enqueued it will run as soon as possible (provided a worker is running). However you can schedule jobs to run in the future, either by a given duration (`_defer_by`) or at a particular time `_defer_until`, see [`arq.connections.ArqRedis.enqueue_job()`](#arq.connections.ArqRedis.enqueue_job "arq.connections.ArqRedis.enqueue_job").

import asyncio
from datetime import datetime, timedelta

from arq import create\_pool
from arq.connections import RedisSettings

async def the\_task(ctx):
    print('this is the tasks, delay since enqueueing:', datetime.now() \- ctx\['enqueue\_time'\])

async def main():
    redis \= await create\_pool(RedisSettings())

    \# deferred by 10 seconds
    await redis.enqueue\_job('the\_task', \_defer\_by\=10)

    \# deferred by 1 minute
    await redis.enqueue\_job('the\_task', \_defer\_by\=timedelta(minutes\=1))

    \# deferred until jan 28th 2032, you'll be waiting a long time for this...
    await redis.enqueue\_job('the\_task', \_defer\_until\=datetime(2032, 1, 28))

class WorkerSettings:
    functions \= \[the\_task\]

if \_\_name\_\_ \== '\_\_main\_\_':
    asyncio.run(main())

### Job Uniqueness[¶](#job-uniqueness "Permalink to this heading")

Sometimes you want a job to only be run once at a time (eg. a backup) or once for a given parameter (eg. generating invoices for a particular company).

_arq_ supports this via custom job ids, see [`arq.connections.ArqRedis.enqueue_job()`](#arq.connections.ArqRedis.enqueue_job "arq.connections.ArqRedis.enqueue_job"). It guarantees that a job with a particular ID cannot be enqueued again until its execution has finished and its result has cleared. To control when a finished job’s result clears, you can use the keep\_result setting on your worker, see [`arq.worker.func()`](#arq.worker.func "arq.worker.func").

import asyncio

from arq import create\_pool
from arq.connections import RedisSettings
from arq.jobs import Job

async def the\_task(ctx):
    print('running the task with id', ctx\['job\_id'\])

async def main():
    redis \= await create\_pool(RedisSettings())

    \# no id, random id will be generated
    job1 \= await redis.enqueue\_job('the\_task')
    print(job1)
    """
    >  <arq job 99edfef86ccf4145b2f64ee160fa3297>
    """

    \# random id again, again the job will be enqueued and a job will be returned
    job2 \= await redis.enqueue\_job('the\_task')
    print(job2)
    """
    >  <arq job 7d2163c056e54b62a4d8404921094f05>
    """

    \# custom job id, job will be enqueued
    job3 \= await redis.enqueue\_job('the\_task', \_job\_id\='foobar')
    print(job3)
    """
    >  <arq job foobar>
    """

    \# same custom job id, job will not be enqueued and enqueue\_job will return None
    job4 \= await redis.enqueue\_job('the\_task', \_job\_id\='foobar')
    print(job4)
    """
    >  None
    """

    \# you can retrieve jobs by using arq.jobs.Job
    await redis.enqueue\_job('the\_task', \_job\_id\='my\_job')
    job5 \= Job(job\_id\='my\_job', redis\=redis)
    print(job5)
    """
    <arq job my\_job>
    """

class WorkerSettings:
    functions \= \[the\_task\]

if \_\_name\_\_ \== '\_\_main\_\_':
    asyncio.run(main())

The check of `job_id` uniqueness in the queue is performed using a redis transaction so you can be certain jobs with the same id won’t be enqueued twice (or overwritten) even if they’re enqueued at exactly the same time.

### Job Results[¶](#job-results "Permalink to this heading")

You can access job information, status and job results using the [`arq.jobs.Job`](#arq.jobs.Job "arq.jobs.Job") instance returned from [`arq.connections.ArqRedis.enqueue_job()`](#arq.connections.ArqRedis.enqueue_job "arq.connections.ArqRedis.enqueue_job").

import asyncio

from arq import create\_pool
from arq.connections import RedisSettings
\# requires \`pip install devtools\`, used for pretty printing of job info
from devtools import debug

async def the\_task(ctx):
    print('running the task')
    return 42

async def main():
    redis \= await create\_pool(RedisSettings())

    job \= await redis.enqueue\_job('the\_task')

    \# get the job's id
    print(job.job\_id)
    """
    >  68362958a244465b9be909db4b7b5ab4 (or whatever)
    """

    \# get information about the job, will include results if the job has finished, but
    \# doesn't await the job's result
    debug(await job.info())
    """
    >   docs/examples/job\_results.py:23 main
    JobDef(
        function='the\_task',
        args=(),
        kwargs={},
        job\_try=None,
        enqueue\_time=datetime.datetime(2019, 4, 23, 13, 58, 56, 781000),
        score=1556027936781
    ) (JobDef)
    """

    \# get the Job's status
    print(await job.status())
    """
    >  JobStatus.queued
    """

    \# poll redis for the job result, if the job raised an exception,
    \# it will be raised here
    \# (You'll need the worker running at the same time to get a result here)
    print(await job.result(timeout\=5))
    """
    >  42
    """

class WorkerSettings:
    functions \= \[the\_task\]

if \_\_name\_\_ \== '\_\_main\_\_':
    asyncio.run(main())

### Retrying jobs and cancellation[¶](#retrying-jobs-and-cancellation "Permalink to this heading")

As described above, when an arq worker shuts down, any ongoing jobs are cancelled immediately (via vanilla `task.cancel()`, so a `CancelledError` will be raised). You can see this by running a slow job (eg. add `await asyncio.sleep(5)`) and hitting `Ctrl+C` once it’s started.

You’ll get something like.

➤  arq slow\_job.WorkerSettings
12:42:38: Starting worker for 1 functions: the\_task
12:42:38: redis\_version=4.0.9 mem\_usage=904.50K clients\_connected=4 db\_keys=3
12:42:38:  10.23s → c3dd4acc171541b9ac10b1d791750cde:the\_task() delayed=10.23s
^C12:42:40: shutdown on SIGINT ◆ 0 jobs complete ◆ 0 failed ◆ 0 retries ◆ 1 ongoing to cancel
12:42:40:   1.16s ↻ c3dd4acc171541b9ac10b1d791750cde:the\_task cancelled, will be run again


➤  arq slow\_job.WorkerSettings
12:42:50: Starting worker for 1 functions: the\_task
12:42:50: redis\_version=4.0.9 mem\_usage=904.61K clients\_connected=4 db\_keys=4
12:42:50:  21.78s → c3dd4acc171541b9ac10b1d791750cde:the\_task() try=2 delayed=21.78s
12:42:55:   5.00s ← c3dd4acc171541b9ac10b1d791750cde:the\_task ●
^C12:42:57: shutdown on SIGINT ◆ 1 jobs complete ◆ 0 failed ◆ 0 retries ◆ 0 ongoing to cancel

You can also retry jobs by raising the [`arq.worker.Retry`](#arq.worker.Retry "arq.worker.Retry") exception from within a job, optionally with a duration to defer rerunning the jobs by:

import asyncio
from httpx import AsyncClient
from arq import create\_pool, Retry
from arq.connections import RedisSettings

async def download\_content(ctx, url):
    session: AsyncClient \= ctx\['session'\]
    response \= await session.get(url)
    if response.status\_code != 200:
        \# retry the job with increasing back-off
        \# delays will be 5s, 10s, 15s, 20s
        \# after max\_tries (default 5) the job will permanently fail
        raise Retry(defer\=ctx\['job\_try'\] \* 5)
    return len(response.text)

async def startup(ctx):
    ctx\['session'\] \= AsyncClient()

async def shutdown(ctx):
    await ctx\['session'\].aclose()

async def main():
    redis \= await create\_pool(RedisSettings())
    await redis.enqueue\_job('download\_content', 'https://httpbin.org/status/503')

class WorkerSettings:
    functions \= \[download\_content\]
    on\_startup \= startup
    on\_shutdown \= shutdown

if \_\_name\_\_ \== '\_\_main\_\_':
    asyncio.run(main())

To abort a job, call `arq.job.Job.abort()`. (Note for the `arq.job.Job.abort()` method to have any effect, you need to set `allow_abort_jobs` to `True` on the worker, this is for performance reason. `allow_abort_jobs=True` may become the default in future)

`arq.job.Job.abort()` will abort a job if it’s already running or prevent it being run if it’s currently in the queue.

import asyncio
from arq import create\_pool
from arq.connections import RedisSettings

async def do\_stuff(ctx):
    print('doing stuff...')
    await asyncio.sleep(10)
    return 'stuff done'

async def main():
    redis \= await create\_pool(RedisSettings())
    job \= await redis.enqueue\_job('do\_stuff')
    await asyncio.sleep(1)
    await job.abort()

class WorkerSettings:
    functions \= \[do\_stuff\]
    allow\_abort\_jobs \= True

if \_\_name\_\_ \== '\_\_main\_\_':
    asyncio.run(main())

### Health checks[¶](#health-checks "Permalink to this heading")

_arq_ will automatically record some info about its current state in redis every `health_check_interval` seconds. That key/value will expire after `health_check_interval + 1` seconds so you can be sure if the variable exists _arq_ is alive and kicking (technically you can be sure it was alive and kicking `health_check_interval` seconds ago).

You can run a health check with the CLI (assuming you’re using the first example above):

arq \--check demo.WorkerSettings

The command will output the value of the health check if found; then exit `0` if the key was found and `1` if it was not.

A health check value takes the following form:

Mar\-01 17:41:22 j\_complete\=0 j\_failed\=0 j\_retried\=0 j\_ongoing\=0 queued\=0

Where the items have the following meaning:

*   `j_complete` the number of jobs completed
    
*   `j_failed` the number of jobs which have failed eg. raised an exception
    
*   `j_ongoing` the number of jobs currently being performed
    
*   `j_retried` the number of jobs retries run
    

### Cron Jobs[¶](#cron-jobs "Permalink to this heading")

Functions can be scheduled to be run periodically at specific times. See [`arq.cron.cron()`](#arq.cron.cron "arq.cron.cron").

from arq import cron

async def run\_regularly(ctx):
    print('run foo job at 9.12am, 12.12pm and 6.12pm')

class WorkerSettings:
    cron\_jobs \= \[
        cron(run\_regularly, hour\={9, 12, 18}, minute\=12)
    \]

Usage roughly shadows [cron](https://helpmanual.io/man8/cron/) except `None` is equivalent on `*` in crontab. As per the example sets can be used to run at multiple of the given unit.

Note that `second` defaults to `0` so you don’t in inadvertently run jobs every second and `microsecond` defaults to `123456` so you don’t inadvertently run jobs every microsecond and so _arq_ avoids enqueuing jobs at the top of a second when the world is generally slightly busier.

### Synchronous Jobs[¶](#synchronous-jobs "Permalink to this heading")

Functions that can block the loop for extended periods should be run in an executor like `concurrent.futures.ThreadPoolExecutor` or `concurrent.futures.ProcessPoolExecutor` using `loop.run_in_executor` as shown below.

import time
import functools
import asyncio
from concurrent import futures

def sync\_task(t):
    return time.sleep(t)

async def the\_task(ctx, t):
    blocking \= functools.partial(sync\_task, t)
    loop \= asyncio.get\_running\_loop()
    return await loop.run\_in\_executor(ctx\['pool'\], blocking)

async def startup(ctx):
    ctx\['pool'\] \= futures.ProcessPoolExecutor()

class WorkerSettings:
    functions \= \[the\_task\]
    on\_startup \= startup

### Custom job serializers[¶](#custom-job-serializers "Permalink to this heading")

By default, _arq_ will use the built-in `pickle` module to serialize and deserialize jobs. If you wish to use an alternative serialization methods, you can do so by specifying them when creating the connection pool and the worker settings. A serializer function takes a Python object and returns a binary representation encoded in a `bytes` object. A deserializer function, on the other hand, creates Python objects out of a `bytes` sequence.

Warning

It is essential that the serialization functions used by [`arq.connections.create_pool()`](#arq.connections.create_pool "arq.connections.create_pool") and [`arq.worker.Worker`](#arq.worker.Worker "arq.worker.Worker") are the same, otherwise jobs created by the former cannot be executed by the latter. This also applies when you update your serialization functions: you need to ensure that your new functions are backward compatible with the old jobs, or that there are no jobs with the older serialization scheme in the queue.

Here is an example with [MsgPack](http://msgpack.org), an efficient binary serialization format that may enable significant memory improvements over pickle:

import asyncio

import msgpack  \# installable with "pip install msgpack"

from arq import create\_pool
from arq.connections import RedisSettings

async def the\_task(ctx):
    return 42

async def main():
    redis \= await create\_pool(
        RedisSettings(),
        job\_serializer\=msgpack.packb,
        job\_deserializer\=lambda b: msgpack.unpackb(b, raw\=False),
    )
    await redis.enqueue\_job('the\_task')

class WorkerSettings:
    functions \= \[the\_task\]
    job\_serializer \= msgpack.packb
    \# refer to MsgPack's documentation as to why raw=False is required
    job\_deserializer \= lambda b: msgpack.unpackb(b, raw\=False)

if \_\_name\_\_ \== '\_\_main\_\_':
    asyncio.run(main())

Reference[¶](#module-arq.connections "Permalink to this heading")
-----------------------------------------------------------------

_class_ arq.connections.RedisSettings(_host: Union\[str, List\[Tuple\[str, int\]\]\] \= 'localhost'_, _port: int \= 6379_, _unix\_socket\_path: Optional\[str\] \= None_, _database: int \= 0_, _username: Optional\[str\] \= None_, _password: Optional\[str\] \= None_, _ssl: bool \= False_, _ssl\_keyfile: Optional\[str\] \= None_, _ssl\_certfile: Optional\[str\] \= None_, _ssl\_cert\_reqs: str \= 'required'_, _ssl\_ca\_certs: Optional\[str\] \= None_, _ssl\_ca\_data: Optional\[str\] \= None_, _ssl\_check\_hostname: bool \= False_, _conn\_timeout: int \= 1_, _conn\_retries: int \= 5_, _conn\_retry\_delay: int \= 1_, _max\_connections: Optional\[int\] \= None_, _sentinel: bool \= False_, _sentinel\_master: str \= 'mymaster'_, _retry\_on\_timeout: bool \= False_, _retry\_on\_error: Optional\[List\[Exception\]\] \= None_, _retry: Optional\[Retry\] \= None_)[\[source\]](/_modules/arq/connections#RedisSettings)[¶](#arq.connections.RedisSettings "Permalink to this definition")

No-Op class used to hold redis connection redis\_settings.

Used by [`arq.connections.create_pool()`](#arq.connections.create_pool "arq.connections.create_pool") and [`arq.worker.Worker`](#arq.worker.Worker "arq.worker.Worker").

_class_ arq.connections.ArqRedis(_pool\_or\_conn: Optional\[ConnectionPool\] \= None_, _job\_serializer: Optional\[Callable\[\[Dict\[str, Any\]\], bytes\]\] \= None_, _job\_deserializer: Optional\[Callable\[\[bytes\], Dict\[str, Any\]\]\] \= None_, _default\_queue\_name: str \= 'arq:queue'_, _expires\_extra\_ms: int \= 86400000_, _\*\*kwargs: Any_)[\[source\]](/_modules/arq/connections#ArqRedis)[¶](#arq.connections.ArqRedis "Permalink to this definition")

Thin subclass of `redis.asyncio.Redis` which adds `arq.connections.enqueue_job()`.

Parameters:

*   **redis\_settings** – an instance of `arq.connections.RedisSettings`.
    
*   **job\_serializer** – a function that serializes Python objects to bytes, defaults to pickle.dumps
    
*   **job\_deserializer** – a function that deserializes bytes into Python objects, defaults to pickle.loads
    
*   **default\_queue\_name** – the default queue name to use, defaults to `arq.queue`.
    
*   **expires\_extra\_ms** – the default length of time from when a job is expected to start after which the job expires, defaults to 1 day in ms.
    
*   **kwargs** – keyword arguments directly passed to `redis.asyncio.Redis`.
    

Initialize a new Redis client. To specify a retry policy for specific errors, first set retry\_on\_error to a list of the error/s to retry on, then set retry to a valid Retry object. To retry on TimeoutError, retry\_on\_timeout can also be set to True.

_async_ enqueue\_job(_function: str_, _\*args: Any_, _\_job\_id: Optional\[str\] \= None_, _\_queue\_name: Optional\[str\] \= None_, _\_defer\_until: Optional\[datetime\] \= None_, _\_defer\_by: Union\[None, int, float, timedelta\] \= None_, _\_expires: Union\[None, int, float, timedelta\] \= None_, _\_job\_try: Optional\[int\] \= None_, _\*\*kwargs: Any_) → Optional\[[Job](#arq.jobs.Job "arq.jobs.Job")\][\[source\]](/_modules/arq/connections#ArqRedis.enqueue_job)[¶](#arq.connections.ArqRedis.enqueue_job "Permalink to this definition")

Enqueue a job.

Parameters:

*   **function** – Name of the function to call
    
*   **args** – args to pass to the function
    
*   **\_job\_id** – ID of the job, can be used to enforce job uniqueness
    
*   **\_queue\_name** – queue of the job, can be used to create job in different queue
    
*   **\_defer\_until** – datetime at which to run the job
    
*   **\_defer\_by** – duration to wait before running the job
    
*   **\_expires** – do not start or retry a job after this duration; defaults to 24 hours plus deferring time, if any
    
*   **\_job\_try** – useful when re-enqueueing jobs within a job
    
*   **kwargs** – any keyword arguments to pass to the function
    

Returns:

[`arq.jobs.Job`](#arq.jobs.Job "arq.jobs.Job") instance or `None` if a job with this ID already exists

_async_ all\_job\_results() → List\[JobResult\][\[source\]](/_modules/arq/connections#ArqRedis.all_job_results)[¶](#arq.connections.ArqRedis.all_job_results "Permalink to this definition")

Get results for all jobs in redis.

_async_ queued\_jobs(_\*_, _queue\_name: Optional\[str\] \= None_) → List\[JobDef\][\[source\]](/_modules/arq/connections#ArqRedis.queued_jobs)[¶](#arq.connections.ArqRedis.queued_jobs "Permalink to this definition")

Get information about queued, mostly useful when testing.

_async_ arq.connections.create\_pool(_settings\_: Optional\[[RedisSettings](#arq.connections.RedisSettings "arq.connections.RedisSettings")\] \= None_, _\*_, _retry: int \= 0_, _job\_serializer: Optional\[Callable\[\[Dict\[str, Any\]\], bytes\]\] \= None_, _job\_deserializer: Optional\[Callable\[\[bytes\], Dict\[str, Any\]\]\] \= None_, _default\_queue\_name: str \= 'arq:queue'_, _expires\_extra\_ms: int \= 86400000_) → [ArqRedis](#arq.connections.ArqRedis "arq.connections.ArqRedis")[\[source\]](/_modules/arq/connections#create_pool)[¶](#arq.connections.create_pool "Permalink to this definition")

Create a new redis pool, retrying up to `conn_retries` times if the connection fails.

Returns a [`arq.connections.ArqRedis`](#arq.connections.ArqRedis "arq.connections.ArqRedis") instance, thus allowing job enqueuing.

arq.worker.func(_coroutine: Union\[str, Function, WorkerCoroutine\]_, _\*_, _name: Optional\[str\] \= None_, _keep\_result: Optional\[SecondsTimedelta\] \= None_, _timeout: Optional\[SecondsTimedelta\] \= None_, _keep\_result\_forever: Optional\[bool\] \= None_, _max\_tries: Optional\[int\] \= None_) → Function[\[source\]](/_modules/arq/worker#func)[¶](#arq.worker.func "Permalink to this definition")

Wrapper for a job function which lets you configure more settings.

Parameters:

*   **coroutine** – coroutine function to call, can be a string to import
    
*   **name** – name for function, if None, `coroutine.__qualname__` is used
    
*   **keep\_result** – duration to keep the result for, if 0 the result is not kept
    
*   **keep\_result\_forever** – whether to keep results forever, if None use Worker default, wins over `keep_result`
    
*   **timeout** – maximum time the job should take
    
*   **max\_tries** – maximum number of tries allowed for the function, use 1 to prevent retrying
    

_exception_ arq.worker.Retry(_defer: Optional\[SecondsTimedelta\] \= None_)[\[source\]](/_modules/arq/worker#Retry)[¶](#arq.worker.Retry "Permalink to this definition")

Special exception to retry the job (if `max_retries` hasn’t been reached).

Parameters:

**defer** – duration to wait before rerunning the job

_class_ arq.worker.Worker(_functions: Sequence\[Union\[Function, WorkerCoroutine\]\] \= ()_, _\*_, _queue\_name: Optional\[str\] \= 'arq:queue'_, _cron\_jobs: Optional\[Sequence\[CronJob\]\] \= None_, _redis\_settings: Optional\[[RedisSettings](#arq.connections.RedisSettings "arq.connections.RedisSettings")\] \= None_, _redis\_pool: Optional\[[ArqRedis](#arq.connections.ArqRedis "arq.connections.ArqRedis")\] \= None_, _burst: bool \= False_, _on\_startup: Optional\[StartupShutdown\] \= None_, _on\_shutdown: Optional\[StartupShutdown\] \= None_, _on\_job\_start: Optional\[StartupShutdown\] \= None_, _on\_job\_end: Optional\[StartupShutdown\] \= None_, _after\_job\_end: Optional\[StartupShutdown\] \= None_, _handle\_signals: bool \= True_, _job\_completion\_wait: int \= 0_, _max\_jobs: int \= 10_, _job\_timeout: SecondsTimedelta \= 300_, _keep\_result: SecondsTimedelta \= 3600_, _keep\_result\_forever: bool \= False_, _poll\_delay: SecondsTimedelta \= 0.5_, _queue\_read\_limit: Optional\[int\] \= None_, _max\_tries: int \= 5_, _health\_check\_interval: SecondsTimedelta \= 3600_, _health\_check\_key: Optional\[str\] \= None_, _ctx: Optional\[Dict\[Any, Any\]\] \= None_, _retry\_jobs: bool \= True_, _allow\_abort\_jobs: bool \= False_, _max\_burst\_jobs: int \= \-1_, _job\_serializer: Optional\[Callable\[\[Dict\[str, Any\]\], bytes\]\] \= None_, _job\_deserializer: Optional\[Callable\[\[bytes\], Dict\[str, Any\]\]\] \= None_, _expires\_extra\_ms: int \= 86400000_, _timezone: Optional\[timezone\] \= None_, _log\_results: bool \= True_)[\[source\]](/_modules/arq/worker#Worker)[¶](#arq.worker.Worker "Permalink to this definition")

Main class for running jobs.

Parameters:

*   **functions** – list of functions to register, can either be raw coroutine functions or the result of [`arq.worker.func()`](#arq.worker.func "arq.worker.func").
    
*   **queue\_name** – queue name to get jobs from
    
*   **cron\_jobs** – list of cron jobs to run, use [`arq.cron.cron()`](#arq.cron.cron "arq.cron.cron") to create them
    
*   **redis\_settings** – settings for creating a redis connection
    
*   **redis\_pool** – existing redis pool, generally None
    
*   **burst** – whether to stop the worker once all jobs have been run
    
*   **on\_startup** – coroutine function to run at startup
    
*   **on\_shutdown** – coroutine function to run at shutdown
    
*   **on\_job\_start** – coroutine function to run on job start
    
*   **on\_job\_end** – coroutine function to run on job end
    
*   **after\_job\_end** – coroutine function to run after job has ended and results have been recorded
    
*   **handle\_signals** – default true, register signal handlers, set to false when running inside other async framework
    
*   **job\_completion\_wait** – time to wait before cancelling tasks after a signal. Useful together with `terminationGracePeriodSeconds` in kubernetes, when you want to make the pod complete jobs before shutting down. The worker will not pick new tasks while waiting for shut down.
    
*   **max\_jobs** – maximum number of jobs to run at a time
    
*   **job\_timeout** – default job timeout (max run time)
    
*   **keep\_result** – default duration to keep job results for
    
*   **keep\_result\_forever** – whether to keep results forever
    
*   **poll\_delay** – duration between polling the queue for new jobs
    
*   **queue\_read\_limit** – the maximum number of jobs to pull from the queue each time it’s polled. By default it equals `max_jobs` \* 5, or 100; whichever is higher.
    
*   **max\_tries** – default maximum number of times to retry a job
    
*   **health\_check\_interval** – how often to set the health check key
    
*   **health\_check\_key** – redis key under which health check is set
    
*   **ctx** – dictionary to hold extra user defined state
    
*   **retry\_jobs** – whether to retry jobs on Retry or CancelledError or not
    
*   **allow\_abort\_jobs** – whether to abort jobs on a call to [`arq.jobs.Job.abort()`](#arq.jobs.Job.abort "arq.jobs.Job.abort")
    
*   **max\_burst\_jobs** – the maximum number of jobs to process in burst mode (disabled with negative values)
    
*   **job\_serializer** – a function that serializes Python objects to bytes, defaults to pickle.dumps
    
*   **job\_deserializer** – a function that deserializes bytes into Python objects, defaults to pickle.loads
    
*   **expires\_extra\_ms** – the default length of time from when a job is expected to start after which the job expires, defaults to 1 day in ms.
    
*   **timezone** – timezone used for evaluation of cron schedules, defaults to system timezone
    
*   **log\_results** – when set to true (default) results for successful jobs will be logged
    

run() → None[\[source\]](/_modules/arq/worker#Worker.run)[¶](#arq.worker.Worker.run "Permalink to this definition")

Sync function to run the worker, finally closes worker connections.

_async_ async\_run() → None[\[source\]](/_modules/arq/worker#Worker.async_run)[¶](#arq.worker.Worker.async_run "Permalink to this definition")

Asynchronously run the worker, does not close connections. Useful when testing.

_async_ run\_check(_retry\_jobs: Optional\[bool\] \= None_, _max\_burst\_jobs: Optional\[int\] \= None_) → int[\[source\]](/_modules/arq/worker#Worker.run_check)[¶](#arq.worker.Worker.run_check "Permalink to this definition")

Run [`arq.worker.Worker.async_run()`](#arq.worker.Worker.async_run "arq.worker.Worker.async_run"), check for failed jobs and raise `arq.worker.FailedJobs` if any jobs have failed.

Returns:

number of completed jobs

_async_ start\_jobs(_job\_ids: List\[bytes\]_) → None[\[source\]](/_modules/arq/worker#Worker.start_jobs)[¶](#arq.worker.Worker.start_jobs "Permalink to this definition")

For each job id, get the job definition, check it’s not running and start it in a task

handle\_sig\_wait\_for\_completion(_signum: Signals_) → None[\[source\]](/_modules/arq/worker#Worker.handle_sig_wait_for_completion)[¶](#arq.worker.Worker.handle_sig_wait_for_completion "Permalink to this definition")

Alternative signal handler that allow tasks to complete within a given time before shutting down the worker. Time can be configured using wait\_for\_job\_completion\_on\_signal\_second. The worker will stop picking jobs when signal has been received.

arq.cron.cron(_coroutine: Union\[str, WorkerCoroutine\]_, _\*_, _name: Optional\[str\] \= None_, _month: Union\[None, Set\[int\], int\] \= None_, _day: Union\[None, Set\[int\], int\] \= None_, _weekday: Union\[None, Set\[int\], int, Literal\['mon', 'tues', 'wed', 'thurs', 'fri', 'sat', 'sun'\]\] \= None_, _hour: Union\[None, Set\[int\], int\] \= None_, _minute: Union\[None, Set\[int\], int\] \= None_, _second: Union\[None, Set\[int\], int\] \= 0_, _microsecond: int \= 123456_, _run\_at\_startup: bool \= False_, _unique: bool \= True_, _job\_id: Optional\[str\] \= None_, _timeout: Optional\[Union\[int, float, timedelta\]\] \= None_, _keep\_result: Optional\[float\] \= 0_, _keep\_result\_forever: Optional\[bool\] \= False_, _max\_tries: Optional\[int\] \= 1_) → CronJob[\[source\]](/_modules/arq/cron#cron)[¶](#arq.cron.cron "Permalink to this definition")

Create a cron job, eg. it should be executed at specific times.

Workers will enqueue this job at or just after the set times. If `unique` is true (the default) the job will only be run once even if multiple workers are running.

Parameters:

*   **coroutine** – coroutine function to run
    
*   **name** – name of the job, if None, the name of the coroutine is used
    
*   **month** – month(s) to run the job on, 1 - 12
    
*   **day** – day(s) to run the job on, 1 - 31
    
*   **weekday** – week day(s) to run the job on, 0 - 6 or mon - sun
    
*   **hour** – hour(s) to run the job on, 0 - 23
    
*   **minute** – minute(s) to run the job on, 0 - 59
    
*   **second** – second(s) to run the job on, 0 - 59
    
*   **microsecond** – microsecond(s) to run the job on, defaults to 123456 as the world is busier at the top of a second, 0 - 1e6
    
*   **run\_at\_startup** – whether to run as worker starts
    
*   **unique** – whether the job should only be executed once at each time (useful if you have multiple workers)
    
*   **job\_id** – ID of the job, can be used to enforce job uniqueness, spanning multiple cron schedules
    
*   **timeout** – job timeout
    
*   **keep\_result** – how long to keep the result for
    
*   **keep\_result\_forever** – whether to keep results forever
    
*   **max\_tries** – maximum number of tries for the job
    

_class_ arq.jobs.JobStatus(_value_, _names\=None_, _\*_, _module\=None_, _qualname\=None_, _type\=None_, _start\=1_, _boundary\=None_)[\[source\]](/_modules/arq/jobs#JobStatus)[¶](#arq.jobs.JobStatus "Permalink to this definition")

Enum of job statuses.

deferred _\= 'deferred'_[¶](#arq.jobs.JobStatus.deferred "Permalink to this definition")

job is in the queue, time it should be run not yet reached

queued _\= 'queued'_[¶](#arq.jobs.JobStatus.queued "Permalink to this definition")

job is in the queue, time it should run has been reached

in\_progress _\= 'in\_progress'_[¶](#arq.jobs.JobStatus.in_progress "Permalink to this definition")

job is in progress

complete _\= 'complete'_[¶](#arq.jobs.JobStatus.complete "Permalink to this definition")

job is complete, result is available

not\_found _\= 'not\_found'_[¶](#arq.jobs.JobStatus.not_found "Permalink to this definition")

job not found in any way

_class_ arq.jobs.Job(_job\_id: str_, _redis: Redis\[bytes\]_, _\_queue\_name: str \= 'arq:queue'_, _\_deserializer: Optional\[Callable\[\[bytes\], Dict\[str, Any\]\]\] \= None_)[\[source\]](/_modules/arq/jobs#Job)[¶](#arq.jobs.Job "Permalink to this definition")

Holds data a reference to a job.

_async_ result(_timeout: Optional\[float\] \= None_, _\*_, _poll\_delay: float \= 0.5_, _pole\_delay: Optional\[float\] \= None_) → Any[\[source\]](/_modules/arq/jobs#Job.result)[¶](#arq.jobs.Job.result "Permalink to this definition")

Get the result of the job or, if the job raised an exception, reraise it.

This function waits for the result if it’s not yet available and the job is present in the queue. Otherwise `ResultNotFound` is raised.

Parameters:

*   **timeout** – maximum time to wait for the job result before raising `TimeoutError`, will wait forever
    
*   **poll\_delay** – how often to poll redis for the job result
    
*   **pole\_delay** – deprecated, use poll\_delay instead
    

_async_ info() → Optional\[JobDef\][\[source\]](/_modules/arq/jobs#Job.info)[¶](#arq.jobs.Job.info "Permalink to this definition")

All information on a job, including its result if it’s available, does not wait for the result.

_async_ result\_info() → Optional\[JobResult\][\[source\]](/_modules/arq/jobs#Job.result_info)[¶](#arq.jobs.Job.result_info "Permalink to this definition")

Information about the job result if available, does not wait for the result. Does not raise an exception even if the job raised one.

_async_ status() → [JobStatus](#arq.jobs.JobStatus "arq.jobs.JobStatus")[\[source\]](/_modules/arq/jobs#Job.status)[¶](#arq.jobs.Job.status "Permalink to this definition")

Status of the job.

_async_ abort(_\*_, _timeout: Optional\[float\] \= None_, _poll\_delay: float \= 0.5_) → bool[\[source\]](/_modules/arq/jobs#Job.abort)[¶](#arq.jobs.Job.abort "Permalink to this definition")

Abort the job.

Parameters:

*   **timeout** – maximum time to wait for the job result before raising `TimeoutError`, will wait forever on None
    
*   **poll\_delay** – how often to poll redis for the job result
    

Returns:

True if the job aborted properly, False otherwise

