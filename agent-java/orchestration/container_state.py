from . import WorkloadState, CRStrategy


class ContainerState(object):
    def __init__(self, workload_state: WorkloadState) -> None:
        self.workload_state = workload_state
        self.request_to_checkpoint = None

    def register_strategy(self, strategy: CRStrategy) -> None:
        self.request_to_checkpoint = strategy.when_to_checkpoint(self.workload_state)

    def register_request(self, latency: int) -> None:
        self.workload_state.register_request(latency=latency)

    @property
    def should_checkpoint(self) -> bool:
        return self.workload_state.request_number == self.request_to_checkpoint

    @property
    def should_evict(self) -> bool:
        return self.workload_state.should_evict
