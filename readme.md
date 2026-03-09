
# A library that adds monitoring to python multiprocessing workloads

File mp.py includes a library, that runs a task with the python multiprocessing library, with a given number of forked processes. The worker processes exit, when no more tasks are available.

I addition to that it does the following:

- Adds an object with shared memory counters, that keeps track of the number of completed tasks, vs number of submitted tasks; number of instances where task threw and exception, the mean execution time of each task, as well as the maximum and minimum of the execution times of each task, the number of currently active worker processes.
- Adds an http server bound to the local interface only, the http server creates a report that includes the counter values.
- The task execution function is monitored for crashes, so that the report is also including the stack traces of these crashes.
- the main process is also printing the same kind of report as reported by the web server, after completing the tasks and exiting the worker processes.

Example usage of this library is in file test.py.

Test run:

```
# to tun the test task
python test.py

# to run the bash script that sends monitoring requests
./test.sh
```

At the end of the test run, the main process will print a report like that (the same kind of report you get from sending an http request, for querying the status) 

```
Main process - all workers finished
Report:

Active workers: 0
Requests submitted: 100
Processed requests: 100
Crashed requests: 4 (out of Processed requests)
Average task duration: 3461 ms
Minimum task duration: 2007 ms
Maximum task duration: 4998 ms

Traceback (most recent call last):
  File "/Users/mz485f/work/mphelper/mp.py", line 10, in wrapper
    data = func(*args, **kwargs)
  File "/Users/mz485f/work/mphelper/test.py", line 17, in example_worker_task
    return 1/0
ZeroDivisionError: division by zero


Traceback (most recent call last):
  File "/Users/mz485f/work/mphelper/mp.py", line 10, in wrapper
    data = func(*args, **kwargs)
  File "/Users/mz485f/work/mphelper/test.py", line 17, in example_worker_task
    return 1/0
ZeroDivisionError: division by zero


Traceback (most recent call last):
  File "/Users/mz485f/work/mphelper/mp.py", line 10, in wrapper
    data = func(*args, **kwargs)
  File "/Users/mz485f/work/mphelper/test.py", line 17, in example_worker_task
    return 1/0
ZeroDivisionError: division by zero


Traceback (most recent call last):
  File "/Users/mz485f/work/mphelper/mp.py", line 10, in wrapper
    data = func(*args, **kwargs)
  File "/Users/mz485f/work/mphelper/test.py", line 17, in example_worker_task
    return 1/0
ZeroDivisionError: division by zero
```

Enjoy!
