from . import WorkloadState
from copy import deepcopy
from minio import Minio
from minio.deleteobjects import DeleteObject
import json


class Checkpoint(object):
    def __init__(
        self,
        state: WorkloadState,
        path: str,
        bucket: str = "checkpoints",
        client: Minio = None,
    ) -> None:
        super().__init__()
        self.bucket = bucket
        self.path = path  # MinIO path prefix
        self.state = deepcopy(state)
        self.client = client

    def __str__(self):
        return f"Checkpoint @ {self.state.request_number}"

    def __repr__(self) -> str:
        return self.__str__()

    def delete(self, client: Minio = None):
        # from https://stackoverflow.com/questions/57664545/how-to-remove-a-path-in-minio-storage-using-python-sdk
        client = client or self.client
        objects_to_delete = client.list_objects(
            self.bucket, prefix=self.path, recursive=True
        )
        objects_to_delete = [DeleteObject(x.object_name) for x in objects_to_delete]
        for del_err in client.remove_objects(self.bucket, objects_to_delete):
            print("Deletion Error: {}".format(del_err))

    def serialize(self) -> str:
        return {
            "bucket": self.bucket,
            "path": self.path,
            "state": self.state.serialize(),
        }

    def deserialize(payload: str, client: Minio):
        # print("Payload:", payload)
        
        # obj = json.loads(payload)
        obj = payload
        return Checkpoint(WorkloadState.deserialize(obj["state"]), obj["path"], obj["bucket"], client)
