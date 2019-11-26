import argparse
import numpy as np

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'lib'))
import resultserializer
import evalutil

def are_same_clusterings(clusterings, garbage):
  # Tuple conversion probably isn't necessary, but it makes everything
  # hashable, so it's probably a good idea.
  _convert_to_tuples = lambda C: tuple([tuple(cluster) for cluster in C])
  first_C = _convert_to_tuples(clusterings[0])
  first_G = tuple(garbage[0])
  for C, G in zip(clusterings[1:], garbage[1:]):
    if _convert_to_tuples(C) != first_C or tuple(G) != first_G:
      return False
  return True

def main():
  parser = argparse.ArgumentParser(
    description='LOL HI THERE',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
  )
  parser.add_argument('neutree_fn')
  parser.add_argument('mutrel_fn')
  args = parser.parse_args()

  neutree = np.load(args.neutree_fn, allow_pickle=True)
  clusterings = neutree['clusterings']
  garbage = neutree['garbage']

  if are_same_clusterings(clusterings, garbage):
    mrel = evalutil.make_mutrel_from_trees_and_single_clustering(neutree['structs'], neutree['logscores'], neutree['counts'], clusterings[0], garbage[0])
  else:
    mrel = evalutil.make_mutrel_from_trees_and_unique_clusterings(neutree['structs'], neutree['logscores'], clusterings, garbage)
  evalutil.save_sorted_mutrel(mrel, args.mutrel_fn)

if __name__ == '__main__':
  main()