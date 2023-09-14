import json

DEFAULT_EVICT_REQUESTS = 1
DEFAULT_MAX_REQUESTS = 200


class Parameters(object):
    def __init__(
        self,
        eviction: int = DEFAULT_EVICT_REQUESTS,
        max_requests: int = DEFAULT_MAX_REQUESTS,
    ) -> None:
        super().__init__()
        self.eviction = eviction
        self.max_requests = max_requests

    def serialize(self) -> str:
        return json.dumps(
            {"eviction": self.eviction, "max_requests": self.max_requests}
        )

    def deserialize(payload: str):
        if not payload:
            return Parameters()

        obj = json.loads(payload)
        return Parameters(eviction=obj["eviction"], max_requests=obj["max_requests"])
