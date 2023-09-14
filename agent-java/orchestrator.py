import logging

from minio import Minio
from minio.error import S3Error
from datetime import datetime

from orchestration import (
    FixedStrategy,
    Parameters,
    Checkpoint,
    ContainerState,
    WorkloadState,
    CRStrategy,
    RequestCentricStrategy,
    ColdStartStrategy,
    cr_deserialize,
)
import hashlib
import json
import time
from typing import Dict, List
from collections import defaultdict
import requests

CHECKPOINTS_BUCKET = "checkpoints"
MAX_RETRIES = 3

client: Minio = None
benchmark: str = None


class CRUD(object):
    # All methods internally track tuple[counter: int, success: bool]
    # but only return the boolean and associated data, if applicable.
    # The boolean tracks whether or not someone has written to the
    # data since then.
    HOST = "database-svc.stores.svc.cluster.local:5000"

    def __init__(self, benchmark: str, simulate_local=False) -> None:
        self.benchmark = benchmark
        # print("Initializing CRUD for", benchmark, "with local store:", simulate_local)
        self.next_expected_id = -1

        # For local store simulation (for testing purposes)
        self.simulate_local = simulate_local
        self.local_store = {}
        self.local_counter = defaultdict(int)
        try:
            with open("local_store.json", "r") as f:
                self.local_store = json.load(f)
        except FileNotFoundError:
            pass

    def _check_id(self, counter: int):
        return self.next_expected_id < 0 or counter == self.next_expected_id

    def read(self) -> "tuple[object, bool]":
        if self.simulate_local:
            count = self.local_counter[self.benchmark]
            data = self.local_store.get(self.benchmark, None)
            # print("Read", data, "from local store")
            passed = self._check_id(count)
            self.next_expected_id = count  # count should be the same after a read
        else:
            try:
                r = requests.get(
                    f"http://{CRUD.HOST}/read/{self.benchmark}",
                    params={"next_expected_id": self.next_expected_id},
                )
                resp = r.json()
                data = resp["data"]
                passed = resp["passed"]
                self.next_expected_id = resp["next_expected_id"]
            except requests.exceptions.RequestException as e:
                print("CRUD: Received container request error:", e)
                data = None
                passed = False

        return data, passed

    # If this returns false, the write does NOT go through
    def write(self, data: object) -> bool:
        if self.simulate_local:
            count = self.local_counter[self.benchmark]
            # print("Write", data, "to local store", count)
            passed = self._check_id(count)
            if passed:
                self.local_counter[self.benchmark] += 1
                self.local_store[self.benchmark] = data
                with open("local_store.json", "w") as f:
                    json.dump(self.local_store, f)
                self.next_expected_id = count + 1  # count should increase after a write
        else:
            try:
                r = requests.post(
                    f"http://{CRUD.HOST}/write/{self.benchmark}",
                    params={"next_expected_id": self.next_expected_id},
                    json=data
                )
                resp = r.json()
                passed = resp["passed"]
                self.next_expected_id = resp["next_expected_id"]
            except requests.exceptions.RequestException as e:
                print("CRUD: Received container request error:", e)
                passed = False


        print("CRUD: Executed write", len(data), self.next_expected_id)
        return passed

    def delete(self) -> bool:
        if self.simulate_local:
            passed = self.benchmark in self.local_store
            if passed:
                del self.local_store[self.benchmark]
                self.local_counter[self.benchmark] = 0
        else:
            try:
                r = requests.get(
                    f"http://{CRUD.HOST}/delete/{self.benchmark}",
                )
                resp = r.json()
                passed = resp["passed"]
                self.next_expected_id = resp["next_expected_id"]
            except requests.exceptions.RequestException as e:
                print("CRUD: Received container request error:", e)
                passed = False

        print("CRUD: Executed delete")
        return passed


def setup_minio():
    global client
    client = Minio(
        "minio-svc.stores.svc.cluster.local:9000",
        access_key="minioadmin",
        secret_key="minioadmin",
        secure=False,
    )

    found = client.bucket_exists(CHECKPOINTS_BUCKET)
    if not found:
        client.make_bucket(CHECKPOINTS_BUCKET)
        print("Created checkpoints bucket")
    else:
        print("Checkpoints bucket already exists")


local_container_state: ContainerState = None


class OrchestratorState(object):
    def __init__(self) -> None:
        self.params: Parameters = None
        self.strategy: CRStrategy = None
        self.state: ContainerState = local_container_state

    def serialize(self) -> str:
        return json.dumps(
            {
                "params": self.params.serialize() if self.params else "",
                "strategy": self.strategy.serialize() if self.strategy else "",
            }
        )

    def deserialize(serialized: str):
        # print(f"Deserialize {serialized}")
        obj = json.loads(serialized) if serialized else dict(params="", strategy="")
        val = OrchestratorState()
        val.params = Parameters.deserialize(obj["params"])
        # val.strategy = CRStrategy.deserialize(obj["strategy"], client)
        val.strategy = cr_deserialize(obj["strategy"], client)
        print("Returned deserialized pool: ", val.strategy.pool)
        return val


setup_minio()
checkpoint_hash = hashlib.sha512()

crud: CRUD = None


def clear_pool():
    # TODO
    pass


def clear_state():
    crud.delete()


def init(using_benchmark: str):
    global benchmark, crud
    benchmark = using_benchmark
    # print("benchmark", benchmark)
    crud = CRUD(benchmark)


init("BFS")  # TODO FOR INTEGRATION: must be passed in from environment


def save_state(state: OrchestratorState) -> bool:
    return crud.write(state.serialize())


def read_state() -> "tuple[OrchestratorState, bool]":
    state, passed = crud.read()
    # print("read_state" state)
    # print(f"read_state {state}")
    if not passed:
        return None, passed
    else:
        return OrchestratorState.deserialize(state), passed


def exponential_retry(fn):
    def wrapped(*args, **kwargs):
        success = False
        data = None
        i = 0
        while not success and i < MAX_RETRIES:
            success, data = fn(*args, **kwargs)

            if not success:
                time.sleep((i + 1) / 2)
                i += 1
                print(f"Request failed, retry #{i}, error: {data}")

        if not success:
            print("ERROR: Hit maximum retries")
            raise OverflowError()

        return success, data

    return wrapped


@exponential_retry
def on_container_started() -> "tuple[bool, object]":
    global local_container_state

    orch, passed = read_state()
    # print("on_container_started", orch, passed)
    if not passed:
        return False, "Could not read orchestrator state"

    checkpoint: Checkpoint = None

    print("Current Pool: ", orch.strategy.pool)

    if orch.strategy.pool:
        checkpoint = orch.strategy.checkpoint_to_use()

    from_checkpoint = checkpoint is not None
    if from_checkpoint:
        starting_req_number = checkpoint.state.request_number
        checkpoint_location = checkpoint.path
    else:
        starting_req_number = 0
        checkpoint_location = ""

    workload_state = WorkloadState(orch.params, starting_req_number)

    local_container_state = ContainerState(workload_state=workload_state)
    orch.state = local_container_state
    orch.state.register_strategy(orch.strategy)

    print("Orchestrator will checkpoint at %s" % orch.state.request_to_checkpoint)

    if save_state(orch):
        return (
            True,
            {
                "success": True,
                "from_checkpoint": from_checkpoint,
                "checkpoint_location": checkpoint_location,
                "will_checkpoint_at": orch.state.request_to_checkpoint,
            },
        )
    else:
        return False, "Could not update orchestrator state"


@exponential_retry
def on_container_request(latency: float) -> "tuple[bool, object]":
    orch, passed = read_state()
    if not passed:
        return False, "Could not read orchestrator state"

    orch.state.register_request(latency=latency)
    orch.strategy.on_request(orch.state.workload_state)

    if save_state(orch):
        should_checkpoint = orch.state.should_checkpoint
        checkpoint_location = ""

        should_evict = orch.state.should_evict

        if should_checkpoint:
            checkpoint_hash.update(bytes(datetime.now().ctime(), encoding="utf8"))
            checkpoint_location = checkpoint_hash.digest().hex()

        return True, {
            "success": True,
            "should_checkpoint": should_checkpoint,
            "checkpoint_location": checkpoint_location,
            "should_evict": should_evict,
        }
    else:
        return False, "Could not update orchestrator state"


# Returns tuple[success: bool, message: str]
@exponential_retry
def on_container_checkpoint(path: str) -> "tuple[bool, str]":
    orch, passed = read_state()
    if not passed:
        return False, "Could not read orchestrator state"

    checkpoint = Checkpoint(orch.state.workload_state, path, client=client)
    orch.strategy.pool.append(checkpoint)
    print("Pool: ", orch.strategy.pool)

    if save_state(orch):
        return (True, "Registered checkpoint!")
    else:
        return False, "Could not update orchestrator state"


# Returns tuple[success: bool, message: str]
def init_params(**params) -> "tuple[bool, str]":
    workload_params = dict()
    desired_params = {"eviction": int, "max_requests": int}
    for item, value in params:
        workload_params[item] = desired_params[item](value)

    state, passed = read_state()
    if not passed:
        return False, "Could not read orchestrator state"

    state.params = Parameters(**workload_params)
    if save_state(state):
        return (
            True,
            f"Initialized parameters: {params.eviction} and {params.max_requests}",
        )
    else:
        return False, "Could not update orchestrator state"


# Returns tuple[success: bool, message: str]
def init_strategy(strategy_type: str, **params) -> "tuple[bool, str]":
    strategy_constructor = None
    desired_params = {}

    if strategy_type == "cold":
        strategy_constructor = ColdStartStrategy
    elif strategy_type == "fixed":
        desired_params = {"request_to_checkpoint": int}
        strategy_constructor = FixedStrategy
    elif strategy_type == "request_centric":
        desired_params = {"p": float, "max_capacity": int, "gamma": float, "eps": float}
        strategy_constructor = RequestCentricStrategy

    if strategy_constructor is None:
        return False, "Unknown strategy type"

    extra_params = {}
    for item, value in params.items():
        if item not in desired_params:
            continue
        extra_params[item] = desired_params[item](value)

    state, passed = read_state()
    if not passed:
        return False, "Could not read orchestrator state"

    strategy = strategy_constructor(
        state.params, [], **extra_params
    )  # pool is presumed empty
    state.strategy = strategy

    if save_state(state):
        return True, f"Initialized {strategy.name}"
    else:
        return False, "Could not update orchestrator state"