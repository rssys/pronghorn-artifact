### Import Packages

import sys
import json
import os
import datetime
import time
import logging
import subprocess
import requests
import uuid
import re

from tqdm import tqdm
from slugify import slugify
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

### Configure Request Adapter

retry_strategy = Retry(total=0)
adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=1, pool_maxsize=1)
http = requests.Session()
http.mount("http://", adapter)

### Generate Benchmark Run UID

uid = datetime.datetime.now().strftime("%m-%d-%H:%M:%S")

### Declare Constants

NUM_REQUESTS = int(sys.argv[1])
REQUEST_DELAY = int(sys.argv[2]) # in ms
test = sys.argv[4]
filename = ""
if sys.argv[3] == "pypy": 
  filename = "python-" + test + ".csv"
else:
   filename = "java-" + test + ".csv"
BENCHMARKS = sys.argv[5:]
STRATEGIES = [
    "cold",
    "fixed&request_to_checkpoint=1",
    "request_centric&max_capacity=12"
]
RATE = [1, 4, 20]
MUTABILITIES = ["1"]

### Configure Logging Handlers

logger = logging.getLogger()
if sys.argv[3] == "pypy": 
  logging.basicConfig(filename="python-" + test + ".log", format='%(asctime)s %(filename)s: %(message)s', filemode='a+')
else:
   logging.basicConfig(filename="java-" + test + ".log", format='%(asctime)s %(filename)s: %(message)s', filemode='a+')
logger.setLevel(logging.DEBUG)

def check_namespace_pods():
    namespace = "openfaas-fn"
    cmd = f"kubectl get pods -n {namespace} --no-headers | wc -l"
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return int(result.stdout.strip())

with open(filename, "a") as output_file:
  for strategy in STRATEGIES:
      for benchmark in BENCHMARKS:
          for rate in RATE:
            for mutability in MUTABILITIES:
  
                logger.info("Deploying %s function", benchmark)
                deploy_cmd = f"faas-cli deploy --image=skharban/{benchmark} --name={benchmark} --env=ENV={strategy},true,{rate}"
                deploy_proc = subprocess.run(deploy_cmd.split(" "), capture_output=True)
                logger.debug("Deploy command response: %s", deploy_proc.stdout.decode("UTF-8"))
                
                time.sleep(5)

                logger.info("Executing strategy: %s for benchmark %s with rate %s and mutability %s", strategy, benchmark, rate, mutability)
                
                nums = re.compile(r"\d+ ms")
                url = f"http://127.0.0.1:8080/function/{benchmark}?mutability={mutability}"
                for index, request in tqdm(enumerate(range(NUM_REQUESTS))):
                  for retry in range(3):
                    retries = 0
                    try:
                      start_time = datetime.datetime.now()
                      response = http.get(url)
                      end_time = datetime.datetime.now()
                      search = nums.search(response.text)
                      if search is None: # PyPy benchmark
                        body = json.loads(response.text)
                        server_side = body.get('server_time')
                        overhead = body.get('client_overhead', 0)
                      else: # Java benchmark
                        server_side = int(search.group(0).split(" ")[0])
                        overhead = 0
                      client_side = (end_time - start_time) / datetime.timedelta(microseconds=1)
                      logger.debug("%s %s %s", server_side, overhead, client_side)
                      
                      output_file.write(f"{index + 1},{benchmark},{mutability},{strategy},{client_side},{server_side},{overhead}\n")
                      time.sleep(REQUEST_DELAY/1000)
                    except:
                      retries += 1
                      time.sleep(min(retries ** 2, 10))
                    else:
                      break
                output_file.flush()
                logger.info("Completed strategy: %s for benchmark %s with mutability %s", strategy, benchmark, mutability)
                clean_cmd = f"faas-cli remove {benchmark}"
                clean_proc = subprocess.run(clean_cmd.split(" "), capture_output=True)
                logger.debug("Clean command response: %s", clean_proc.stdout.decode("UTF-8"))

                # Update the delete and redeploy commands
                delete_cmd = f"kubectl delete -f {os.path.expanduser('~/pronghorn-artifact/database/pod.yaml')}"
                delete_proc = subprocess.run(delete_cmd.split(" "), capture_output=True)
                logger.debug("Delete command response: %s", delete_proc.stdout.decode("UTF-8"))

                redeploy_cmd = f"kubectl apply -f {os.path.expanduser('~/pronghorn-artifact/database/pod.yaml')}"
                redeploy_proc = subprocess.run(redeploy_cmd.split(" "), capture_output=True)
                logger.debug("Redeploy command response: %s", redeploy_proc.stdout.decode("UTF-8"))

                # Check if there are pods in the openfaas-fn namespace
                while check_namespace_pods() > 0:
                    print("Waiting for pods to terminate...")
                    time.sleep(10)