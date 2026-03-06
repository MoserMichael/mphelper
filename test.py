import random
import time
import multiprocessing
import os
import mp

def example_worker_task(task): 
    # very important processing stuff comes here.
    sleep_time = random.uniform(2, 5)
    time.sleep(sleep_time)


# task callback has to conform to the same form:
# can't abstract that away, as 
# - per worker task must init its own resources (in the real world)
# - passing the task class around processes is.. challenging
# - want to keep task callback local to the worker process, don't want to loose that.

def task_cb(task_queue, counters): 
    print(f"Worker: {os.getpid()} start worker")
    
    while True:
        task = task_queue.get()
        
        if task is None:
            print(f"Worker: {os.getpid()} - get null task")
            task_queue.task_done()
            break

        start = time.monotonic_ns()
        
        # the function that does the worker task
        example_worker_task(task)

        duration = time.monotonic_ns() - start
        duration_ms = duration // 1000000

        task_queue.task_done()
        counters.inc_completed(duration_ms)

    print(f"Worker: {os.getpid()} exit worker")
    counters.dec_workers()


def run_system():
    with multiprocessing.Manager() as manager:
        
        # multiprocessor helper with statistics + http server to query stats.
        mph = mp.MultiprocessingHelper(num_process=10, process_cb=task_cb, manager=manager, http_port=8080)
        
        # generate workload
        for idx in range(0, 100):
            task_msg = (idx)
            mph.post(task_msg)
        
        # wrap it up - tell workers to finish & close workers & wait for completion
        mph.finish()

# with multiprocessing: must run the command via this check.
# doesn't run without it.
if __name__ == '__main__':
    run_system()
