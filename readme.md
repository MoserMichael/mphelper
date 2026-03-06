
# A library that adds monitoring to python multiprocessing workloads

File mp.py includes a library, that runs a task with the python multiprocessing library, with a given number of forked processes. The worker processes exit, when no more tasks are available.

I addition to that it does the following:

- Adds an object with shared memory counters, that keeps track of the number of completed tasks, vs number of submitted tasks; number of instances where task threw and exception, the mean execution time of each task, as well as the maximum and minimum of the execution times of each task, the number of currently active worker processors.
- Adds an http server bound to the local interface only, the http server creates a report that includes the counter values.
- The task execution function is monitored for crashes, so that the report is also including the stack traces of these crashes.

Example usage of this library is in file test.py.

Enjoy!
