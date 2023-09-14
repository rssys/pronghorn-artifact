from datetime import  datetime                                                   
import random                                                      
from jinja2 import Template

SEED = 42
MIN_ITEMS = 10000
MAX_ITEMS = 50000
SCALING_FACTOR = (MAX_ITEMS + MIN_ITEMS) / 20

random.seed(SEED)

def _generate_workload(mutability):
  nextGaussian = random.gauss((MIN_ITEMS + MAX_ITEMS)/2, (mutability ** 0.5) * SCALING_FACTOR)
  if nextGaussian < MIN_ITEMS:
    return MIN_ITEMS
  if nextGaussian > MAX_ITEMS:
    return MAX_ITEMS
  return nextGaussian

def generate_input(mutability):
    input_config = {'username': 'Pronghorn'} 
    input_config['items'] = int(_generate_workload(mutability))
    return input_config

def handle(mutability):
    event = generate_input(mutability)
    name = event.get('username')
    size = event.get('items')
    start = datetime.now()
    cur_time = datetime.now()
    random_numbers = random.sample(range(0, 1000000), size)
    template = Template(open('resource/template.html', 'r').read())
    html = template.render(username = name, cur_time = cur_time, random_numbers = random_numbers)
    end = datetime.now()
    return {
        'server_time': (end - start).microseconds,
        'mutability': mutability,
        'size': size,
    }