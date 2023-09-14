from typing import List, Union

from .. import Parameters, CRStrategy, Checkpoint, WorkloadState
import random


class ColdStartStrategy(CRStrategy):
    def __init__(self, workload: Parameters, pool: List[Checkpoint]) -> None:
        super().__init__(workload, pool)

    @property
    def name(self) -> str:
        return f"ColdStart"

    def checkpoint_to_use(self) -> Checkpoint:
        return None

    def when_to_checkpoint(self, state: WorkloadState) -> int:
        return 50000

    def on_request(self, state: WorkloadState):
        pass

    def on_eviction(
        self, checkpoint: Union[Checkpoint, None], final_state: WorkloadState
    ) -> None:
        pass

    def reset(self):
        self.pool = []
