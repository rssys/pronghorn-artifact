import os
import sys
from pathlib import Path
import subprocess
import time

from orchestrator import (
    on_container_started,
    on_container_checkpoint,
    on_container_request,
)

from minio import Minio
from minio.error import S3Error
from datetime import datetime

LOG_FNAME = "requestLog.txt"
CHECKPOINTS_BUCKET = "checkpoints"


client: Minio = None


def setup_minio():
    print("Setting up MinIO...")

    global client
    client = Minio(
        "minio-svc.store.svc.cluster.local:9000",
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


def get_pypy_pid():
    return subprocess.check_output("pgrep pypy3", shell=True).decode(
        sys.stdout.encoding
    )


def get_java_pid():
    return subprocess.check_output("pgrep java", shell=True).decode(sys.stdout.encoding)


def after_request(latency):
    passed, state = on_container_request(
        float(latency)
    )  # execute_callback(CallbackRoutes.REQUEST, params={"latency": latency})
    if state["should_checkpoint"]:
        pid = get_java_pid()
        cmd = f"rm -rf checkpoint && mkdir -p checkpoint && criu dump -t {pid.strip()} -v3 --tcp-established --leave-running -D ./checkpoint"
        if os.system(cmd):
            print("Checkpointing failed!")
            sys.exit(1)
        else:
            path = state["checkpoint_location"]
            print("Checkpointing succeeded! Uploading to MinIO...")
            for root, dirs, files in os.walk("./checkpoint"):
                for file in files:
                    file_path = os.path.join(root, file)
                    print("Uploading", file, "at", file_path)
                    client.fput_object(
                        CHECKPOINTS_BUCKET, f"{path}/{file}", file_path=file_path
                    )

            on_container_checkpoint(path)

    if state["should_evict"] and False:
        print("Received eviction notice")
        pid = get_java_pid()
        os.system(f"kill -9 {pid}")
        # os.system("killall pypy3")
        # print("Killed Python Process")
        os.system("killall java")
        print("Killed Java process")
        sys.exit(0)


def init():
    print("Executing start callback")
    passed, state = on_container_started()
    print("Callback response:", state)

    try:
        Path(LOG_FNAME).unlink()
    except FileNotFoundError:
        pass
    Path(LOG_FNAME).touch()

    if state["from_checkpoint"]:
        dir = "./restore"
        os.system("rm -rf ./restore")
        os.system("mkdir restore")
        objects_to_retrieve = client.list_objects(
            CHECKPOINTS_BUCKET, prefix=state["checkpoint_location"], recursive=True
        )
        for obj in objects_to_retrieve:
            name: str = obj.object_name
            filename = name.split("/", maxsplit=1)[1]
            client.fget_object(CHECKPOINTS_BUCKET, name, f"{dir}/{filename}")

        cmd = f"criu restore --restore-detached --tcp-close -d -v3 -D {dir}"
    else:
        # cmd = "setsid java -Xmx128m -Xms128m com.openfaas.entrypoint.App < /dev/null &> app.log &"
        cmd = "setsid java -XX:-UsePerfData -Xmx128m -Xms128m com.openfaas.entrypoint.App < /dev/null &> /dev/null &"
        # cmd = "setsid pypy3 index.py < /dev/null &> /dev/null &"

    print("Executing command:", cmd)
    if os.system(cmd):
        print("Init command failed")
        sys.exit(1)


if __name__ == "__main__":
    setup_minio()
    init()

    last_count = 0
    while True:
        with open(LOG_FNAME, "r") as fp:
            contents = fp.readlines()
            count = len(contents)
            if count > last_count:
                for latency in contents[last_count:]:
                    latency = latency.strip()
                    if not latency:
                        continue
                    print("Detected latency:", latency)
                    after_request(latency)
                last_count = count

        time.sleep(10 / 1000)  # 10 ms
