import random
import datetime
import networkx as nx

SEED = 42
MIN_ITEMS = 10
MAX_ITEMS = 1000
SCALING_FACTOR = 10

random.seed(SEED)


def _generate_workload(mutability):
  nextGaussian = random.gauss((MIN_ITEMS + MAX_ITEMS)/2, (mutability ** 0.5) * SCALING_FACTOR)
  if nextGaussian < MIN_ITEMS:
    return MIN_ITEMS
  if nextGaussian > MAX_ITEMS:
    return MAX_ITEMS
  return nextGaussian

def generate_input(mutability):
    return { 'size': int(_generate_workload(mutability)) }

def handle(mutability):

    event = generate_input(mutability)

    size = event.get('size')

    graph_generating_begin = datetime.datetime.now()
    graph = nx.barabasi_albert_graph(size, 10)
    graph_generating_end = datetime.datetime.now()

    process_begin = datetime.datetime.now()
    result = nx.minimum_spanning_tree(graph)
    process_end = datetime.datetime.now()

    graph_generating_time = (graph_generating_end - graph_generating_begin) / datetime.timedelta(microseconds=1)
    process_time = (process_end - process_begin) / datetime.timedelta(microseconds=1)
    return {
            'mutability': mutability,
            'size': size,
            'server_time': process_time,
            'client_overhead': graph_generating_time
    }