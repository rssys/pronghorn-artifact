import os
import sys
import math
import random
import datetime
import urllib.request
from function.storage import storage

SEED = 42
MIN_ITEMS = 1
MAX_ITEMS = 3
SCALING_FACTOR = 10 # To be decided

random.seed(SEED)

url_generators = {
    # source: mlperf fake_imagenet.sh. 230 kB
    'test' : 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e7/Jammlich_crop.jpg/800px-Jammlich_crop.jpg',
    # video: Unsplash Image, 2.4 MB
    'small': 'https://upload.wikimedia.org/wikipedia/commons/7/7b/The_ExTrA_telescopes_at_La_Silla.jpg',
    # resnet model from pytorch. 98M
    'large':  'https://download.pytorch.org/models/resnet50-19c8e357.pth'
}

store = storage()
client = store.client

def _generate_workload(mutability):
  nextGaussian = random.gauss((MIN_ITEMS + MAX_ITEMS)/2, (mutability ** 0.5) / SCALING_FACTOR)
  if nextGaussian < MIN_ITEMS:
    return MIN_ITEMS
  if nextGaussian > MAX_ITEMS:
    return MAX_ITEMS
  return nextGaussian

def generate_input(mutability):
    input_config = {'object': {}, 'bucket': {}}
    input_map = ['test', 'small', 'large']
    size = math.floor(_generate_workload(mutability))
    input_config['object']['url'] = url_generators[input_map[size - 1]]
    input_config['bucket']['output'] = "120.uploader"
    return input_config

def create_resouces():
    if (client.bucket_exists("120.uploader")) == False:
        client.make_bucket("120.uploader")

def clean_resources(bucket, object_name):
  client.remove_object(bucket, object_name)

def handle(mutability):
    create_resouces()
    event = generate_input(mutability)
    output_bucket = event.get('bucket').get('output')
    url = event.get('object').get('url')
    name = os.path.basename(url)
    download_path = '/tmp/{}'.format(name)

    process_begin = datetime.datetime.now()
    urllib.request.urlretrieve(url, filename=download_path)
    size = os.path.getsize(download_path)
    process_end = datetime.datetime.now()

    upload_begin = datetime.datetime.now()
    key_name = store.upload(output_bucket, name, download_path)
    upload_end = datetime.datetime.now()

    process_time = (process_end - process_begin) / datetime.timedelta(microseconds=1)
    upload_time = (upload_end - upload_begin) / datetime.timedelta(microseconds=1)
    clean_resources(output_bucket, key_name)
    return {
      'mutability': mutability,
      'size': size,
      'server_time': upload_time,
      'client_overhead': process_time
    }