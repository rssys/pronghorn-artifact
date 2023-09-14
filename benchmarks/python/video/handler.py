import os
import sys
import glob
import stat
import math
import random
import datetime
import subprocess
import urllib.request
from function.storage import storage

SEED = 42
MIN_ITEMS = 1
MAX_ITEMS = 3
SCALING_FACTOR = 10 # To be decided

random.seed(SEED)

store = storage()
client = store.client
SCRIPT_DIR = "/usr/local/bin"

def _generate_workload(mutability):
  nextGaussian = random.gauss((MIN_ITEMS + MAX_ITEMS)/2, (mutability ** 0.5) / SCALING_FACTOR)
  if nextGaussian < MIN_ITEMS:
    return MIN_ITEMS
  if nextGaussian > MAX_ITEMS:
    return MAX_ITEMS
  return nextGaussian

def clean_resources(bucket, object_name):
  client.remove_object(bucket, object_name)

def create_resouces():
    if (client.bucket_exists("220.video-in") == False ):
        client.make_bucket("220.video-in")
    if (client.bucket_exists("220.video-out") == False ):
        client.make_bucket("220.video-out")

def generate_input(data_dir, input_buckets, output_buckets, upload_func):
    input_config = {'object': {}, 'bucket': {}}
    for file in glob.glob(os.path.join(data_dir, '*.mp4')):
        img = os.path.relpath(file, data_dir)
        input_config['object']['key'] = img
        upload_func(input_buckets[0], img, file)
    input_config['object']['op'] = 'watermark'
    input_config['object']['duration'] = 1
    input_config['bucket']['input'] = input_buckets[0]
    input_config['bucket']['output'] = output_buckets[0]
    return input_config

def call_ffmpeg(args):
    ret = subprocess.call(['ffmpeg', '-y'] + args,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    if ret != 0:
        print('Invocation of ffmpeg failed!')
        print('Out: ', ret.stdout.decode('utf-8'))
        raise RuntimeError()

# https://superuser.com/questions/556029/how-do-i-convert-a-video-to-gif-using-ffmpeg-with-reasonable-quality
def to_gif(video, duration, event):
    output = '/tmp/processed-{}.gif'.format(os.path.basename(video))
    call_ffmpeg(["-i", video,
        "-t",
        "{0}".format(duration),
        "-vf",
        "fps=10,scale=320:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse",
        "-loop", "0",
        output])
    return output

# https://devopstar.com/2019/01/28/serverless-watermark-using-aws-lambda-layers-ffmpeg/
def watermark(video, duration, event):
    output = '/tmp/processed-{}'.format(os.path.basename(video))
    watermark_file = os.path.dirname(os.path.realpath(__file__))
    call_ffmpeg([
        "-i", video,
        "-i", os.path.join(watermark_file, 'watermark.png'),
        "-t", "{0}".format(duration),
        "-filter_complex", "overlay=main_w/2-overlay_w/2:main_h/2-overlay_h/2",
        output])
    return output

def transcode_mp3(video, duration, event):
    pass

operations = { 'transcode' : transcode_mp3, 'extract-gif' : to_gif, 'watermark' : watermark }

def handle(mutability):
    create_resouces()
    event = generate_input(data_dir="resource",
                            input_buckets=["220.video-in"],
                            output_buckets=["220.video-out"],
                            upload_func=store.upload)
    input_bucket = event.get('bucket').get('input')
    output_bucket = event.get('bucket').get('output')
    key = event.get('object').get('key')
    duration = event.get('object').get('duration')
    op = event.get('object').get('op')
    reps = int(_generate_workload(mutability))
    download_path = '/tmp/{}'.format(key)
    ffmpeg_binary = os.path.join(SCRIPT_DIR, 'ffmpeg')
    try:
        st = os.stat(ffmpeg_binary)
        os.chmod(ffmpeg_binary, st.st_mode | stat.S_IEXEC)
    except OSError:
        pass

    download_begin = datetime.datetime.now()
    store.download(input_bucket, key, download_path)
    download_size = os.path.getsize(download_path)
    download_stop = datetime.datetime.now()

    process_begin = datetime.datetime.now()
    for num in range(reps):
        upload_path = operations[op](download_path, duration, event)
        process_end = datetime.datetime.now()
    upload_begin = datetime.datetime.now()
    filename = os.path.basename(upload_path)
    upload_size = os.path.getsize(upload_path)
    store.upload(output_bucket, filename, upload_path)
    upload_stop = datetime.datetime.now()

    download_time = (download_stop - download_begin) / datetime.timedelta(microseconds=1)
    upload_time = (upload_stop - upload_begin) / datetime.timedelta(microseconds=1)
    process_time = (process_end - process_begin) / datetime.timedelta(microseconds=1)
    clean_resources(input_bucket, key)
    clean_resources(output_bucket, filename)
    return {
            'result': {
                'bucket': output_bucket,
                'key': filename
            },
            'measurement': {
                'download_time': download_time,
                'download_size': download_size,
                'upload_time': upload_time,
                'upload_size': upload_size,
                'compute_time': process_time
            }
        }
