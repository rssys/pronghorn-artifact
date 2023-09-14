from typing import List, Union

from .. import Parameters, CRStrategy, Checkpoint, WorkloadState, FixedStrategy
import random
import numpy as np
import copy

DEFAULT_MAX_CAPACITY = 14

DEFAULT_P = 0.40
DEFAULT_GAMMA = 0.10

DEFAULT_PERFORMANCE_FN = lambda arr: np.mean(np.array(arr))
# DEFAULT_PERFORMANCE_FN = lambda arr: np.median(np.array(arr))

DEFAULT_EPSILON = 0.5
MIN_WEIGHT_EPSILON = 1  # microseconds (median latency)


class RequestCentricStrategy(CRStrategy):
    def __init__(
        self,
        workload: Parameters,
        pool: List[Checkpoint],
        max_capacity: int = DEFAULT_MAX_CAPACITY,
        p: float = DEFAULT_P,
        gamma: float = DEFAULT_GAMMA,
        performance_fn=DEFAULT_PERFORMANCE_FN,
        eps=DEFAULT_EPSILON,
    ) -> None:
        super().__init__(workload, pool)
        self.max_capacity = max_capacity
        self.p = p
        self.gamma = gamma
        self.performance_fn = performance_fn
        self.weights = np.array([0] * workload.max_requests)
        self.eps = eps

    @property
    def name(self) -> str:
        return f"RequestCentric{self.max_capacity}_P{self.p}_Gamma{self.gamma}"

    @property
    def strategy(self) -> str:
        return "RequestCentric"

    def _weights_for(self, req_num, scalar=False):
        cur_slice = self.weights[
            req_num : min(req_num + self.workload.eviction, self.workload.max_requests)
        ]
        output = 1000000.0 / (cur_slice + MIN_WEIGHT_EPSILON)
        if scalar:
            output = self.performance_fn(output)
        return output

    def _prune_pool(self):
        output = []
        by_performance = sorted(
            self.pool,
            key=lambda c: self._weights_for(c.state.request_number, scalar=True),
            reverse=True,
        )

        keeping_p = round(self.p * len(by_performance))
        output += by_performance[:keeping_p]
        by_performance = by_performance[keeping_p:]

        keeping_gamma = round(self.gamma * len(by_performance))
        output += random.choices(
            by_performance, k=min(keeping_gamma, len(by_performance))
        )

        output_chkpts = {chkpt for chkpt in output}
        removed = [chkpt for chkpt in self.pool if chkpt not in output_chkpts]
        for chkpt in removed:
            chkpt.delete()

        self.pool[:] = output
        print(
            f"Evicted all but top {keeping_p} by performance and {keeping_gamma} by random"
        )
        assert len(self.pool) <= self.max_capacity

    def checkpoint_to_use(self) -> Checkpoint:
        if len(self.pool) > self.max_capacity:
            self._prune_pool()

        print(f"Exploiting")
        expanded_pool = self.pool + [None]
        weights = [
            self._weights_for(
                chkpt.state.request_number if chkpt is not None else 0, scalar=True
            )
            for chkpt in expanded_pool
        ]
        weights = np.array(weights)
        weights_max = np.amax(weights, keepdims=True)
        weights_shifted = np.exp(weights - weights_max)
        weights = weights_shifted / np.sum(weights_shifted, keepdims=True)
        weights = weights.tolist()
        print(list(zip(weights, expanded_pool)))
        ret_val = random.choices(expanded_pool, weights=weights, k=1)[0]
        print("Choosing", ret_val)
        return ret_val

    def when_to_checkpoint(self, state: WorkloadState) -> int:
        # weights = []
        # if self.temperature >= random.uniform(0, 1):  # explore
        #     print("Checkpoint exploring")
        #     weights = cur_slice
        # else:  # exploit
        #     print("Checkpoint exploiting")
        weights = self._weights_for(state.request_number + 1)
        print(
            self.weights,
            weights,
            "Num Weights: ",
            len(weights),
            "Req Num: ",
            state.request_number,
            "Workload Dict: ",
            self.workload.__dict__,
        )
        interval = list(
            range(state.request_number + 1, state.request_number + len(weights) + 1)
        )
        weights = [self._weights_for(i, scalar=True) for i in interval]
        desired_request = random.choices(
            interval,
            # weights=weights.tolist(),
            weights=weights,
            k=1,
        )[0]

        print(f"Checkpointing at {desired_request}", list(zip(interval, weights)))
        fixed_strat = FixedStrategy(self.workload, self.pool, desired_request)
        return fixed_strat.when_to_checkpoint(state)

    def on_request(self, state: WorkloadState):
        request_num = state.request_number - 1
        cur_weight = self.weights[request_num]
        if cur_weight == 0:
            self.weights[request_num] = state.latencies[-1]
        else:
            self.weights[request_num] = (
                self.eps * state.latencies[-1] + (1 - self.eps) * cur_weight
            )

        self.weights[-1] = self.weights[-2]

    def reset(self) -> None:
        for chkpt in self.pool:
            chkpt.delete()
        self.pool[:] = []
        self.weights = np.array([0] * self.workload.max_requests)

    @property
    def extra_state(self) -> dict:
        return {
            "max_capacity": self.max_capacity,  # = max_capacity
            "p": self.p,  # = p
            "gamma": self.gamma,  # = gamma
            "weights": self.weights.tolist(),  # = np.array([0] * workload.max_requests)
            "eps": self.eps,  # = eps
        }
