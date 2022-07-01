import json, os, queue, requests, time
from dotenv import load_dotenv
from threading import Thread
from typing import List

load_dotenv()

# core config
HOST = os.getenv('HOST')
PORT = os.getenv('PORT')
USER = os.getenv('USER')
PRYV_URL = os.getenv('PRYV_URL')
TOKEN = os.getenv('TOKEN')
STREAM = os.getenv('STREAM')
LIMIT = os.getenv('LIMIT')

# test config
URL = f'{HOST}:{PORT}/{USER}.{PRYV_URL}/events?streams={STREAM}&limit={LIMIT}'
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
            start_time = time.time()
            response = make_a_request(URL)
            duration = round(time.time() - start_time, 2)
            result = Result(job_id, response.status_code, duration)
            self.results.append(result)
            self.queue.task_done()
            print(f'Worker #{self.id} finished job #{job_id}')

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
    for result in results:
        if result.status_code == 200:
            number_of_successes += 1
        total_duration += result.duration

    number_of_failures = len(results) - number_of_successes
    average_request_time = round(total_duration / len(results), 2)

    print_title('results', caps=True)
    print(f'{NUMBER_OF_WORKERS} Workers, performing {NUMBER_OF_REQUESTS} requests, finished in {total_duration} seconds!')
    print('-----------------------------')
    print('# of requests : ', len(results))
    print('# of successes : ', number_of_successes)
    print('# of failures : ', number_of_failures)
    print('Average request time : ', average_request_time, ' seconds')


def get_simple_request_time():
    start = time.time()
    response = make_a_request(URL)
    if did_request_succeed(response):
        basic_request_time = round(time.time() - start, 2)
        print('Single request time : ', basic_request_time, ' seconds\n')


def make_a_request(url: str) -> requests.Response:
    headers = {'AUTHORIZATION': TOKEN}
    return requests.get(url=url, headers=headers)

def setup():
    print_title('set-up')



def print_response(response: requests.Response):
    response_dict = json.loads(response.text)
    print('===============================')
    print('RESPONSE : ')
    print('-------------------------------')
    for i in response_dict:
        print(f'\t[{i}] : {response_dict[i]}')
    print('===============================')


def print_title(title: str, caps: bool = False):
    if caps: title = title.upper()
    print(f'\n=== {title} ===\n')


def did_request_succeed(response: requests.Response) -> bool:
    if response.status_code == 200: return True
    else: return False

test()