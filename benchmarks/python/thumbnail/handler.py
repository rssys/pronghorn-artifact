import glob
import io
import os
import sys
import math
import random
import datetime
import urllib.request
from PIL import Image
from function.storage import storage

SEED = 42
MIN_ITEMS = 1
MAX_ITEMS = 5
SCALING_FACTOR = 5 # To be decided

random.seed(SEED)

store = storage()
client = store.client

def _generate_workload(mutability):
  nextGaussian = random.gauss((MIN_ITEMS + MAX_ITEMS)/2, (mutability ** 0.5) / SCALING_FACTOR)
  if nextGaussian < MIN_ITEMS:
    return MIN_ITEMS
  if nextGaussian > MAX_ITEMS:
    return MAX_ITEMS
  return nextGaussian

def create_resouces():
    if (client.bucket_exists("210.thumbnailer-in") == False ):
        client.make_bucket("210.thumbnailer-in")
    if (client.bucket_exists("210.thumbnailer-out") == False ):
        client.make_bucket("210.thumbnailer-out")

def clean_resources(bucket, object_name):
  client.remove_object(bucket, object_name)

def generate_input(data_dir, input_buckets, output_buckets, upload_func):
    input_config = {'object': {}, 'bucket': {}}
    for file in glob.glob(os.path.join(data_dir, '*.jpg')):
        img = os.path.relpath(file, data_dir)
        input_config['object']['key'] = img
        upload_func(input_buckets[0], img, file)
    input_config['object']['width'] = 200
    input_config['object']['height'] = 200
    input_config['bucket']['input'] = input_buckets[0]
    input_config['bucket']['output'] = output_buckets[0]
    return input_config

def resize_image(image_bytes, w, h):
    with Image.open(io.BytesIO(image_bytes)) as image:
        image.thumbnail((w,h))
        out = io.BytesIO()
        image.save(out, format='jpeg')
        out.seek(0)
        return out

def handle(mutability):
    create_resouces()
    event = generate_input(data_dir="resource",
                              input_buckets=["210.thumbnailer-in"],
                              output_buckets=["210.thumbnailer-out"],
                              upload_func=store.upload)
    input_bucket = event.get('bucket').get('input')
    output_bucket = event.get('bucket').get('output')
    key = event.get('object').get('key')
    width = event.get('object').get('width')
    height = event.get('object').get('height')
    reps = int(_generate_workload(mutability))

    download_begin = datetime.datetime.now()
    img = store.download_stream(input_bucket, key)
    download_end = datetime.datetime.now()

    process_begin = datetime.datetime.now()
    # Workload Variance
    for num in range(reps):
        resized = resize_image(img, width, height)
        resized_size = resized.getbuffer().nbytes
    process_end = datetime.datetime.now()

    upload_begin = datetime.datetime.now()
    key_name = store.upload_stream(output_bucket, key, resized)
    upload_end = datetime.datetime.now()

    download_time = (download_end - download_begin) / datetime.timedelta(microseconds=1)
    upload_time = (upload_end - upload_begin) / datetime.timedelta(microseconds=1)
    process_time = (process_end - process_begin) / datetime.timedelta(microseconds=1)
    clean_resources(input_bucket, key)
    clean_resources(output_bucket, key_name)
    return {
            'result': {
                'bucket': output_bucket,
                'key': key_name
            },
            'measurement': {
                'download_time': download_time,
                'download_size': len(img),
                'upload_time': upload_time,
                'upload_size': resized_size,
                'compute_time': process_time
            },
            'reps': reps
    }
