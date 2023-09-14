from typing import List
import json
from . import Parameters


class WorkloadState(object):
    def __init__(self, workload: Parameters, request_number: int) -> None:
        super().__init__()
        self.workload = workload
        self.request_number = request_number
        self.request_counter = 0
        self.latencies = []

    def register_request(self, latency: int):
        self.request_number += 1
        self.request_counter += 1
        self.latencies.append(latency)

    @property
    def should_evict(self) -> bool:
        return (
            self.request_counter >= self.workload.eviction
            or self.request_number >= self.workload.max_requests
        )

    def serialize(self) -> str:
        return {
            "workload": self.workload.serialize(),
            "request_number": self.request_number,
            "request_counter": self.request_counter,
            "latencies": self.latencies,
        }

    def deserialize(payload: str):
        # obj = json.loads(payload)
        obj = payload

        state = WorkloadState(Parameters.deserialize(obj["workload"]), obj["request_number"])
        state.request_counter = obj["request_counter"]
        state.latencies = obj["latencies"]
        return state
