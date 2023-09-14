from . import Checkpoint, WorkloadState, Parameters
from typing import List, Union
import json


class CRStrategy(object):
    def __init__(self, workload: Parameters, pool: List[Checkpoint]) -> None:
        super().__init__()
        self.workload = workload
        self.pool: List[Checkpoint] = pool

    @property
    def name(self) -> str:
        raise NotImplementedError()

    @property
    def strategy(self) -> str:
        return self.name

    def checkpoint_to_use(self) -> Checkpoint:
        raise NotImplementedError()

    def when_to_checkpoint(self, state: WorkloadState) -> int:
        raise NotImplementedError()

    def on_request(self, state: WorkloadState) -> None:
        raise NotImplementedError()

    def register_checkpoint(self, checkpoint: Checkpoint) -> None:
        self.pool.append(checkpoint)

    def on_eviction(
        self, checkpoint: Union[Checkpoint, None], final_state: WorkloadState
    ) -> None:
        raise NotImplementedError()

    def get_pool(self) -> List[Checkpoint]:
        return self.pool

    def reset(self) -> None:
        raise NotImplementedError()

    @property
    def common_state(self) -> dict:
        return {
            "workload": self.workload.serialize(),
            "pool": [chkpt.serialize() for chkpt in self.pool],
            "name": self.name,
            "strategy": self.strategy,
        }

    @property
    def extra_state(self) -> dict:
        return {}

    def serialize(self) -> str:
        return json.dumps({**self.common_state, **self.extra_state})
    
    # def deserialize(self, payload: str):
    #     return cr_deserialize(payload)

    # def deserialize(payload: str, client: Minio):
    #     if not payload:
    #         return FixedStrategy(
    #             Parameters(), [], 5
    #         )  # TODO FOR INTEGRATION: sensible defaults

    #     obj = json.loads(payload)
    #     workload = Parameters.deserialize(obj["workload"])
    #     pool = [Checkpoint.deserialize(chkpt, client) for chkpt in obj["pool"]]
    #     strategy = obj["strategy"]
    #     if strategy == "ColdStart":
    #         return ColdStartStrategy(workload, pool)
    #     elif strategy == "Fixed":
    #         return FixedStrategy(workload, pool, obj["request_to_checkpoint"])
    #     elif strategy == "RequestCentric":
    #         strategy = RequestCentricStrategy(
    #             workload,
    #             pool,
    #             obj["max_capacity"],
    #             obj["p"],
    #             obj["gamma"],
    #             eps=obj["eps"],
    #         )
    #         strategy.weights = np.array(obj["weights"])
    #         return strategy
