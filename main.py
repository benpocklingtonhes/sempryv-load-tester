import os
import queue
import requests
import time
import warnings

from dotenv import load_dotenv
from threading import Thread
from typing import List

from requests.exceptions import ConnectionError
from urllib3.exceptions import ProtocolError

load_dotenv()

# core config
HOST = os.getenv('HOST')
USER = os.getenv('USER')
PRYV_URL = os.getenv('PRYV_URL')
TOKEN = os.getenv('TOKEN')
STREAM = os.getenv('STREAM')
LIMIT = os.getenv('LIMIT')

# test config
URL = f'{HOST}/{USER}.{PRYV_URL}/events?streams={STREAM}&limit={LIMIT}'
NUMBER_OF_WORKERS = int(os.getenv('NUMBER_OF_WORKERS'))
NUMBER_OF_REQUESTS = int(os.getenv('NUMBER_OF_REQUESTS'))


class Worker(Thread):
    def __init__(self, worker_id, q):
        Thread.__init__(self)
        self.id = worker_id
        self.queue = q
        self.results = []

    def run(self):
        while not self.queue.empty():
            job_id = self.queue.get()
            start_time = time.time() * 1000
            try:
                response = make_a_request(URL)
                duration = round(time.time() * 1000 - start_time, 2)
                result = Result(job_id, response.status_code, duration)
                self.results.append(result)
                self.queue.task_done()
                print(f'Worker #{self.id} finished job #{job_id}')
            except (TimeoutError, ConnectionError, ProtocolError):
                warnings.warn(f'WARNING : Job #{job_id} has failed!')


class Result:
    def __init__(self, job_id, status_code, duration):
        self.id = job_id
        self.status_code = status_code
        self.duration = duration


def test():
    print_title('starting load test', caps=True)
    get_simple_request_time()
    q = queue.Queue()

    # fill the queue with jobs
    for job_id in range(NUMBER_OF_REQUESTS):
        q.put(job_id)

    # init of workers
    workers = []
    for i in range(NUMBER_OF_WORKERS):
        print('Starting worker #' + str(i))
        worker = Worker(i, q)
        worker.start()
        workers.append(worker)

    for worker in workers:
        worker.join()

    results = []
    for worker in workers:
        results.extend(worker.results)

    print_title('finished all jobs!', caps=True)
    analysis(results)


def analysis(results: List[Result]):
    number_of_successes = 0
    total_duration = 0
    max_request_time = 0
    min_request_time = 999999

    for result in results:
        if result.status_code == 200:
            number_of_successes += 1
        if result.duration > max_request_time:
            max_request_time = result.duration
        elif result.duration < min_request_time:
            min_request_time = result.duration
        total_duration += result.duration

    total_duration = int(total_duration)
    average_request_time = int(total_duration / NUMBER_OF_REQUESTS)
    max_request_time = int(max_request_time)
    min_request_time = int(min_request_time)
    success_rate = round(number_of_successes / NUMBER_OF_REQUESTS, 2)

    print_title('results', caps=True)
    print(
        f'{NUMBER_OF_WORKERS} Workers, performing {NUMBER_OF_REQUESTS} '
        f'requests, finished in {total_duration} milliseconds!'
    )
    print('-----------------------------')
    print('# of requests : ', NUMBER_OF_REQUESTS)
    print('# of concurrent users : ', NUMBER_OF_WORKERS)
    print('Success rate : ', (success_rate * 100), '%')
    print('Average request time : ', average_request_time, ' milliseconds')
    print('Min request time : ', min_request_time, ' milliseconds')
    print('Max request time : ', max_request_time, ' milliseconds')


def get_simple_request_time():
    start = time.time()
    response = make_a_request(URL)
    if did_request_succeed(response):
        basic_request_time = round(time.time() - start, 2)
        print('Single request time : ', basic_request_time, ' seconds\n')


def make_a_request(url: str) -> requests.Response:
    headers = {'AUTHORIZATION': TOKEN}
    return requests.get(url=url, headers=headers)


def print_title(title: str, caps: bool = False):
    if caps:
        title = title.upper()
    print(f'\n=== {title} ===\n')


def did_request_succeed(response: requests.Response) -> bool:
    if response.status_code == 200:
        return True
    else:
        return False


test()
