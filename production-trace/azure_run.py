#!/usr/bin/python

import os
import abc
import concurrent.futures
import sys
import time
import requests
from kubernetes import client, config
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import argparse

# Maximum number of idle containers.
max_idle_container = 0
# Maximum number of active containers.
max_active_container = 50
# Number of the last millisecond of a day.
end_day = 1000 * 60 * 60 * 24
# Container keep-alive timeout in milliseconds.
keepalive = 1000 * 60 * 10
# Number of milliseconds to add to current time between each iteration.
timestep = 1000
# Maximum number of retries for HTTP requests.
max_retries = 3

retry_strategy = Retry(total=0)
adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=1, pool_maxsize=1)
http = requests.Session()
http.mount("http://", adapter)


class RequestFailedException(Exception):
    pass


class AzureTraceReplayer(abc.ABC):
    # Number of created containers.
    containers = 0
    # Maps container id to function id.
    active_container = {}
    # Maps container id to function id.
    function_container = {}
    # Maps container id to the timestamp of where it should be killed.
    idle_container = {}
    # Current time in seconds.
    current_time = 0
    # Total evictions.
    total_evictions = 0
    # Total invocations.
    total_invocations = 0
    total_cold_starts = 0

    @abc.abstractmethod
    def invoke_function(self, container, function, ms_duration):
        pass

    @abc.abstractmethod
    def new_worker(self, container, function):
        pass

    @abc.abstractmethod
    def evict_worker(self, container):
        pass

    def wait_timestep(self):
        time.sleep(timestep / 1000)

    def invoke_wrapper(self, container, function, ms_duration):
        self.invoke_function(container, function, ms_duration)
        self.active_container.pop(container)
        self.idle_container[container] = self.current_time + keepalive

    def handle_invocation(self, executor, function, ms_duration, workload, strategy):
        def find_available_container(function):
            for container in list(self.idle_container):
                if self.function_container[container] == function:
                    return container

        container = find_available_container(function)
        if not container:
            container = "c{cid}f{fid}".format(cid=self.containers, fid=function)
            self.new_worker(container, function, workload, strategy)
            self.function_container[container] = function
            self.containers += 1
        else:
            self.idle_container.pop(container)

        # Invoke function.
        self.active_container[container] = function
        executor.submit(
            self.invoke_wrapper,
            container=container,
            function=function,
            ms_duration=ms_duration,
        )

    def check_container_eviction(self):
        def evict_container(container):
            self.function_container.pop(container)
            self.idle_container.pop(container)
            self.evict_worker(container)

        def find_evictable_containers():
            to_evict = []
            next_eviction = self.current_time + keepalive
            next_eviction_container = None
            for container in list(self.idle_container):
                timeout = self.idle_container[container]
                if self.current_time >= timeout:
                    to_evict.append(container)
                else:
                    if timeout <= next_eviction:
                        next_eviction = timeout
                        next_eviction_container = container
            return to_evict, next_eviction, next_eviction_container

        # Find the next container to be evicted.
        to_evict, next_eviction, next_eviction_container = find_evictable_containers()

        # Evict containers whose timeout has passed.
        for container in to_evict:
            evict_container(container)

        # If we have too many containers, keep evict the oldest until we have less.
        while len(self.idle_container) > max_idle_container:
            _, next_eviction, next_eviction_container = find_evictable_containers()
            evict_container(next_eviction_container)

        return next_eviction

    @classmethod
    def find_next_invocation(self, file):
        line = file.readline()
        if line:
            _, function, _, ms_duration, ms_timestamp = line.split(",")
            next_invocation = int(ms_timestamp)
        else:
            next_invocation = end_day
            function = None
            ms_duration = None
        return next_invocation, function, ms_duration

    def run(self, dataset, workload, strategy):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            with open(dataset) as file:
                # Skip the header line.
                file.readline()

                # Next container eviction in seconds.
                next_eviction = keepalive

                # Load next invocation and the function that will be invoked.
                next_invocation, function, ms_duration = self.find_next_invocation(file)

                # Advance initial time to the first invocation.
                self.current_time = next_invocation

                while self.current_time < end_day:
                    # Check if we should issue the next invocation.
                    while next_invocation <= self.current_time:
                        if len(self.active_container) >= max_active_container:
                            pass
                        else:
                            self.handle_invocation(executor, function, ms_duration, workload, strategy)
                        (
                            next_invocation,
                            function,
                            ms_duration,
                        ) = self.find_next_invocation(file)

                    # Check if we should evict a container.
                    if (
                        next_eviction <= self.current_time
                        or len(self.idle_container) > max_idle_container
                    ):
                        next_eviction = self.check_container_eviction()

                    # If there are no active workers and no more invocations, jump to the end of the day.
                    if len(self.active_container) == 0 and next_invocation == end_day:
                        self.current_time = next_eviction  # TODO - fixme?
                    else:
                        self.current_time += timestep

                    # Advance to the next second.
                    self.wait_timestep()
                    print(
                        "[{time}] active workers = {active}, idle workers = {idle}, next invocation = {ninvocation}, next eviction = {neviction}".format(
                            time=self.current_time,
                            active=len(self.active_container),
                            idle=len(self.idle_container),
                            ninvocation=next_invocation,
                            neviction=next_eviction,
                        )
                    )


class LogAzureTraceReplayer(AzureTraceReplayer):
    # For the log replayer, we speed up time by 10x.
    time_speed = 10

    def invoke_function(self, container, function, ms_duration):
        print(
            "[{time}] Invoking function {function} (#active = {active}, #idle = {idle})".format(
                time=self.current_time,
                function=function,
                active=len(self.active_container),
                idle=len(self.idle_container),
            )
        )
        time.sleep(float(ms_duration) / 1000 / self.time_speed)

    def new_worker(self, container, function):
        print(
            "[{time}] New worker {cid} for function {fid}".format(
                time=self.current_time, cid=container, fid=function
            )
        )

    def evict_worker(self, container):
        print(
            "[{time}] Evicting worker {cid}.".format(
                time=self.current_time, cid=container
            )
        )

    def wait_timestep(self):
        time.sleep(timestep / 1000 / self.time_speed)


class OpenFaaSAzureTraceReplayer(AzureTraceReplayer):
    def invoke_function(self, container, _, ms_duration):
        container = container[0:32]
        print(
            "[{time}] Invoking function {function} (#active = {active}, #idle = {idle})".format(
                time=self.current_time,
                function=container,
                active=len(self.active_container),
                idle=len(self.idle_container),
            )
        )
        retries = 0
        for _ in range(max_retries):
            try:
                start_time = time.time()
                response = http.get(
                    "http://127.0.0.1:8080/function/{name}?mutability=1".format(
                        name=container
                    )
                )
                end_time = time.time()
                elapsed_time = (end_time - start_time) * 1000
                if response.status_code != 200:
                    raise RequestFailedException(
                        "Request failed with status code: {code}".format(
                            code=response.status_code
                        )
                    )
                else:
                    print(
                        "[{time}] Response: {code} {body}".format(
                            time=self.current_time,
                            code=response.status_code,
                            body=response.text,
                        )
                    )
                    print(
                        "[{time}] Latency: {elapsed_time} ms".format(
                            time=self.current_time,
                            elapsed_time=elapsed_time,
                        )
                    )
                    break  # Exit the loop if the request is successful
            except Exception as e:
                print(
                    "[{time}] Retrying {name} {retries}/{max_retries} - Error: {error}".format(
                        time=self.current_time,
                        name=container,
                        retries=retries,
                        max_retries=max_retries,
                        error=str(e),
                    )
                )
                retries += 1
                time.sleep(min(retries**2, 10))
        self.total_invocations += 1

    def new_worker(self, container, function, workload, strategy):
        container = container[0:32]
        os.system(
            "faas-cli deploy --image=skharban/{workload} --name={name} --env ENV=\"{strategy},false,1\"".format(
                name=container, function=function, workload=workload, strategy=strategy
            )
        )
        self.total_cold_starts += 1
        print("[{time}] New worker {cid}".format(time=self.current_time, cid=container))
        config.load_kube_config()
        v1 = client.CoreV1Api()
        namespace = "openfaas-fn"
        ready = False
        while not ready:
            pod_list = v1.list_namespaced_pod(namespace)
            for pod in pod_list.items:
                if pod.metadata.name.startswith(container):
                    if pod.status.container_statuses:
                        container_status = pod.status.container_statuses[0]
                        if container_status.ready and container_status.state.running:
                            ready = True
                            break
            time.sleep(1)
        print(
            "[{time}] Pod {pod_name} is ready".format(
                time=self.current_time, pod_name=container
            )
        )

    def evict_worker(self, container):
        container = container[0:32]
        os.system("faas-cli remove {name}".format(name=container))
        print(
            "[{time}] Evicting worker {cid}.".format(
                time=self.current_time, cid=container
            )
        )
        self.total_evictions += 1


parser = argparse.ArgumentParser(description="Azure trace replayer.")
parser.add_argument("-w", "--workload", type=str, help="workload")
parser.add_argument("-s", "--strategy", type=str, help="Strategy")
parser.add_argument("-t", "--trace", type=str, help="Azure invocation trace.")
parser.add_argument(
    "-b",
    "--backend",
    type=str,
    default="log",
    help="Which replayer to use: log openfaas",
)
args = parser.parse_args()

if args.backend == "log":
    replayer = LogAzureTraceReplayer()
elif args.backend == "openfaas":
    replayer = OpenFaaSAzureTraceReplayer()
else:
    parser.print_help()
    sys.exit(0)

if not args.trace:
    parser.print_help()
    sys.exit(0)

replayer.run(args.trace, args.workload, args.strategy)
ratio = replayer.total_evictions / replayer.total_invocations
print("Total Cold Starts:", replayer.total_cold_starts)
print("Total Evictions:", replayer.total_evictions)
print("Total Invocations:", replayer.total_invocations)
print("Eviction-to-Invocation Ratio:", ratio)
