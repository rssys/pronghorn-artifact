import os
import subprocess
import time
import numpy as np
import sys


def get_directory_size(path="."):
    total = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total += os.path.getsize(fp)
    return total


dump_times = []
restore_times = []
directory_sizes = []

for i in range(10):
    # get the pid
    pid = subprocess.check_output("pgrep pypy3", shell=True).decode(sys.stdout.encoding)

    # perform the dump
    start = time.time()
    subprocess.run(f"rm -rf checkpoint && mkdir -p checkpoint", shell=True)
    subprocess.run(
        f"criu dump -t {pid.strip()} -v3 --tcp-established --leave-running -D ./checkpoint",
        shell=True,
    )
    end = time.time()
    dump_times.append((end - start) * 1000)  # record in milliseconds

    # calculate directory size
    directory_sizes.append(
        get_directory_size("./checkpoint") / (1024 * 1024)
    )  # record in MB

    # kill the process
    subprocess.run(f"kill {pid.strip()}", shell=True)

    # restore the process
    start = time.time()
    subprocess.run(
        "criu restore --restore-detached --tcp-close -d -v3 -D ./checkpoint", shell=True
    )
    end = time.time()
    restore_times.append((end - start) * 1000)  # record in milliseconds

    time.sleep(2)  # Sleep for 2 seconds

# print mean and standard deviation
print("Mean dump time: ", np.mean(dump_times), "+/-", np.std(dump_times))
print("Mean restore time: ", np.mean(restore_times), "+/-", np.std(restore_times))
print(
    "Mean checkpoint directory size: ",
    np.mean(directory_sizes),
    "+/-",
    np.std(directory_sizes),
    "MB",
)
