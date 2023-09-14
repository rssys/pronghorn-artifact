import os
import io
import glob
import random
import datetime
import shutil
import uuid
import zlib
import sys
from function.storage import storage

SEED = 42
MIN_ITEMS = 1
MAX_ITEMS = 3
SCALING_FACTOR = 10 # To be decided

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

def clean_resources(bucket, object_name):
  client.remove_object(bucket, object_name)

def upload_files(data_root, data_dir, upload_func, input_bucket):

    for root, dirs, files in os.walk(data_dir):
        prefix = os.path.relpath(root, data_root)
        for file in files:
            file_name = prefix + '/' + file
            filepath = os.path.join(root, file)
            upload_func(input_bucket, file_name, filepath)

def generate_input(data_dir, input_buckets, output_buckets, upload_func):

    datasets = []
    for dir in os.listdir(data_dir):
        datasets.append(dir)
        upload_files(data_dir, os.path.join(data_dir, dir), upload_func, input_buckets[0])
    input_config = {'object': {}, 'bucket': {}}
    input_config['object']['key'] = datasets[0]
    input_config['bucket']['input'] = input_buckets[0]
    input_config['bucket']['output'] = output_buckets[0]
    return input_config

def create_resources():
    if (client.bucket_exists("311.compression-in") == False ):
        client.make_bucket("311.compression-in")
    if (client.bucket_exists("311.compression-out") == False ):
        client.make_bucket("311.compression-out")

def parse_directory(directory):

    size = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            size += os.path.getsize(os.path.join(root, file))
    return size

def handle(mutability):
    create_resources()
    event = generate_input(data_dir="resource",
                            input_buckets=["311.compression-in"],
                            output_buckets=["311.compression-out"],
                            upload_func=store.upload)
    input_bucket = event.get('bucket').get('input')
    output_bucket = event.get('bucket').get('output')
    key = event.get('object').get('key')
    download_path = '/tmp/{}-{}'.format(key, uuid.uuid4())
    os.makedirs(download_path)

    s3_download_begin = datetime.datetime.now()
    store.download_directory(input_bucket, key, download_path)
    s3_download_stop = datetime.datetime.now()
    size = parse_directory(download_path)

    compress_begin = datetime.datetime.now()
    shutil.make_archive(os.path.join(download_path, key), 'zip', root_dir=download_path)
    compress_end = datetime.datetime.now()

    s3_upload_begin = datetime.datetime.now()
    archive_name = '{}.zip'.format(key)
    archive_size = os.path.getsize(os.path.join(download_path, archive_name))
    key_name = store.upload(output_bucket, archive_name, os.path.join(download_path, archive_name))
    s3_upload_stop = datetime.datetime.now()

    download_time = (s3_download_stop - s3_download_begin) / datetime.timedelta(microseconds=1)
    upload_time = (s3_upload_stop - s3_upload_begin) / datetime.timedelta(microseconds=1)
    process_time = (compress_end - compress_begin) / datetime.timedelta(microseconds=1)
    clean_resources(input_bucket, key)
    clean_resources(output_bucket, key_name)
    return {
        'mutability': mutability,
        'size': archive_size,
        'server_time': process_time,
        'client_overhead': upload_time
        }
