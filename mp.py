import multiprocessing
from http.server import HTTPServer, BaseHTTPRequestHandler
from functools import wraps
import traceback

def catch_exception(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            data = func(*args, **kwargs)
            return { 'status': True, 'data': data, 'error': None, 'stack_trace': None }
        except Exception as e:
            stack_trace = traceback.format_exc()
            return { 'status': False, 'data': None, 'error': e, 'stack_trace': stack_trace }
    return wrapper
                    

class CounterHandler(BaseHTTPRequestHandler):
    def __init__(self, counters, *args, **kwargs):
        self.counters = counters
        super().__init__(*args, **kwargs)

    # don't want to have incoming requests logged to screen, add your logging here, if you need that
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        #self.wfile.write("Hello world!".encode())
        self.wfile.write(self.get_report())
        #self.wfile.write("Hello world!".encode())

    def get_report(self):
        processed = self.counters.get_counters()
        workers =  processed['active_workers']
        num_reqs = processed['posted_requests']
        c_tasks = processed['completed_tasks']
        crash_tasks = processed['crashed_tasks']
        c_tasks_dur = processed['complete_tasks_duration_sum']
        min_task_duration = processed['min_task_duration']
        max_task_duration = processed['max_task_duration']
        error_text = processed['error_list']

        avg_dur = 0
        min_dur = 0
        max_dur = 0
        if num_reqs != 0:
            avg_dur = c_tasks_dur // num_reqs
            min_dur = min_task_duration
            max_dur = max_task_duration

        msg = f"""
Active workers: {workers}        
Requests submitted: {num_reqs}
Processed requests: {c_tasks}
Crashed requests: {crash_tasks} (out of Processed requests)
Average task duration: {avg_dur} ms
Minimum task duration: {min_dur} ms
Maximum task duration: {max_dur} ms

{error_text}
"""
        return msg.encode()
                
def run_server(counters):
    # Use a lambda to pass our shared objects into the handler's __init__
    def handler(*args, **kwargs): 
        return CounterHandler(counters, *args, **kwargs)
    server = HTTPServer(('localhost', counters.get_port()), handler)
    server.serve_forever()

def init_reporting_server(counters):

    server_proc = multiprocessing.Process(target=run_server, args=(counters,))
    #server_proc.daemon = True  # This makes it a "background" process
    server_proc.start()

    return server_proc


class Counters:
    def __init__(self, http_port):
        self.tasks_counter_lock = None
        self.complete_tasks_duration_sum = None
        self.complete_tasks_counter = None
        self.crashed_tasks_counter = None
        self.posted_requests = None
        self.active_workers = None
        self.min_task_duration = None 
        self.max_task_duration = None
        self.error_list = None 

        self.report_port = http_port
        
    def create(self, manager):
        # changed from worker processes
        self.tasks_counter_lock = manager.Lock()
        self.complete_tasks_duration_sum = manager.Value('i', 0)
        self.complete_tasks_counter = manager.Value('i', 0)
        self.crashed_tasks_counter = manager.Value('i', 0)
        self.active_workers = manager.Value('i', 0)
        self.posted_requests = manager.Value('i', 0)
        self.min_task_duration = manager.Value('i', -1) 
        self.max_task_duration = manager.Value('i', 0)
        self.error_list = manager.list()
            
    def add_posted_requests(self, to_add):
        with self.tasks_counter_lock:
            self.posted_requests.value += to_add

    def inc_completed(self, task_duration, res):
        with self.tasks_counter_lock:
            self.complete_tasks_counter.value += 1
            self.complete_tasks_duration_sum.value += int(task_duration)

            if self.min_task_duration.value == -1:
                self.min_task_duration.value = task_duration
            else:
                self.min_task_duration.value = min(task_duration, self.min_task_duration.value) 

            status = res.get('status')
            if status is not None and status is False:
                self.crashed_tasks_counter.value = self.crashed_tasks_counter.value + 1
                stack = res.get('stack_trace')
                if stack:
                    self.error_list.append(stack)
            
            self.max_task_duration.value = max(task_duration, self.max_task_duration.value) 

    def set_workers(self, num):
        with self.tasks_counter_lock:
            self.active_workers.value = num

    def dec_workers(self):
        with self.tasks_counter_lock:
            self.active_workers.value -= 1

    def get_counters(self):
        ret = {}
        with self.tasks_counter_lock:
            ret= {
                'active_workers': self.active_workers.value,
                'posted_requests': self.posted_requests.value,
                'completed_tasks': self.complete_tasks_counter.value,
                'crashed_tasks': self.crashed_tasks_counter.value,
                'complete_tasks_duration_sum': self.complete_tasks_duration_sum.value,
                'min_task_duration': self.min_task_duration.value,
                'max_task_duration': self.max_task_duration.value,
                'error_list' : "\n\n".join(self.error_list)
            }
        return ret 

    def get_port(self):
        return self.report_port

class MultiprocessingHelper:
    def __init__(self, num_process, process_cb, http_port, manager):
        self.num_processes = num_process
        self.processes = []
        
        self.counters = Counters(http_port)
        self.counters.create(manager)

        self.http_worker = init_reporting_server(self.counters)

        self.q = multiprocessing.JoinableQueue()
        for i in range(self.num_processes):
            p = multiprocessing.Process(target=process_cb, args=(self.q,self.counters,)) 
            p.start()
            self.processes.append(p)
        self.counters.set_workers(self.num_processes)            

    def post(self, task):
        self.q.put(task)
        self.counters.add_posted_requests(1)

    def finish(self):

        for _ in range(self.num_processes):
            self.q.put(None)
        
        self.q.join()
        print("Main process - all posted tasks done")
        
        for p in self.processes:
            p.join()

        self.http_worker.terminate()            

        print("Main process - all workers finished")


