from . import ColdStartStrategy, FixedStrategy, RequestCentricStrategy
from . import Checkpoint, Parameters
import json
import os
from minio import Minio
import numpy as np


def cr_deserialize(payload: str, client: Minio):
    if not payload:
        # TODO FOR INTEGRATION: sensible defaults
        strategy_env = os.getenv("ENV").split(",")[0]
        print(f"Using strategy: {strategy_env}")
        if strategy_env == "cold":
            return ColdStartStrategy(Parameters(), [])
        elif strategy_env == "fixed&request_to_checkpoint=1":
            return FixedStrategy(Parameters(), [], 1)
        else:
            return RequestCentricStrategy(Parameters(), [])
    obj = json.loads(payload)
    workload = Parameters.deserialize(obj["workload"])
    pool = [Checkpoint.deserialize(chkpt, client) for chkpt in obj["pool"]]
    print("Deserialized pool: ", pool)
    strategy = obj["strategy"]
    if strategy == "ColdStart":
        return ColdStartStrategy(workload, pool)
    elif strategy == "Fixed":
        return FixedStrategy(workload, pool, obj["request_to_checkpoint"])
    elif strategy == "RequestCentric":
        strategy = RequestCentricStrategy(
            workload,
            pool,
            obj["max_capacity"],
            obj["p"],
            obj["gamma"],
            eps=obj["eps"],
        )
        strategy.weights = np.array(obj["weights"])
        return strategy
