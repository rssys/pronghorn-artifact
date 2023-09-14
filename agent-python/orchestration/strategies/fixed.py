from typing import Union

from .. import Parameters, CRStrategy, Checkpoint, WorkloadState
from typing import List
import random

DEFAULT_CHECKPOINT_REQUEST = 100


class FixedStrategy(CRStrategy):
    def __init__(
        self,
        workload: Parameters,
        pool: List[Checkpoint],
        request_to_checkpoint: int = DEFAULT_CHECKPOINT_REQUEST,
    ) -> None:
        super().__init__(workload, pool)
        self.request_to_checkpoint = request_to_checkpoint

    @property
    def name(self) -> str:
        return f"Fixed{self.request_to_checkpoint}"

    @property
    def strategy(self) -> str:
        return "Fixed"

    def checkpoint_to_use(self) -> Checkpoint:
        # Pick whichever checkpoint has the closest request number
        # less than or equal to our target
        pool = self.get_pool()
        filtered = [
            (i, chkpt)
            for i, chkpt in enumerate(pool)
            if chkpt.state.request_number <= self.request_to_checkpoint
        ]
        if not filtered:
            chkpt_num = random.randrange(0, len(pool))
        else:
            ordered = sorted(
                filtered,
                key=lambda chkpt: self.request_to_checkpoint
                - chkpt[1].state.request_number,
            )
            chkpt_num, _ = ordered[0]

        print(f"Using checkpoint #{chkpt_num + 1} of {len(pool)}")
        return pool[chkpt_num]

    def when_to_checkpoint(self, state: WorkloadState) -> int:
        workload = state.workload
        lo, hi = state.request_number, state.request_number + workload.eviction
        if lo <= self.request_to_checkpoint <= hi:
            # If we can get to our target this iteration, great!
            return self.request_to_checkpoint
        elif lo <= self.request_to_checkpoint:
            # If we're too low, then get as high as we can
            return hi
        else:
            # If we overshot, we can't do anything
            return lo

    def on_request(self, state: WorkloadState):
        pass

    def on_eviction(
        self, checkpoint: Union[Checkpoint, None], final_state: WorkloadState
    ) -> None:
        pass

    def reset(self):
        self.pool = []

    @property
    def extra_state(self) -> dict:
        return {"request_to_checkpoint": self.request_to_checkpoint}
