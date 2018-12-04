import argparse
import os
import numpy as np
import scipy.integrate
import warnings
import random
import multiprocessing

import common
import pairwise
import inputparser
import tree_sampler
import phi_fitter
import clustermaker
import resultserializer
import plotter

def fit_phis(adjm, supervars, superclusters, tidxs, iterations, parallel):
  ntrees = len(adjm)
  nsamples = len(next(iter(supervars.values()))['total_reads'])

  N, K, S = ntrees, len(superclusters), nsamples
  eta = np.ones((N, K, S))
  phi = np.ones((N, K, S))

  for tidx in tidxs:
    phi[tidx,:,:], eta[tidx,:,:] = phi_fitter.fit_phis(
      adjm[tidx],
      superclusters,
      supervars,
      iterations,
      parallel
    )

  return (phi, eta)

def main():
  np.set_printoptions(linewidth=400, precision=3, threshold=np.nan, suppress=True)
  np.seterr(divide='raise', invalid='raise')
  warnings.simplefilter('ignore', category=scipy.integrate.IntegrationWarning)

  parser = argparse.ArgumentParser(
    description='LOL HI THERE',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
  )
  parser.add_argument('--seed', dest='seed', type=int)
  parser.add_argument('--parallel', dest='parallel', type=int, default=None)
  parser.add_argument('--params', dest='params_fn')
  parser.add_argument('--trees-per-chain', dest='trees_per_chain', type=int, default=1000)
  parser.add_argument('--tree-chains', dest='tree_chains', type=int, default=None)
  parser.add_argument('--phi-iterations', dest='phi_iterations', type=int, default=1000)
  parser.add_argument('ssm_fn')
  parser.add_argument('results_fn')
  args = parser.parse_args()

  # Note that multiprocessing.cpu_count() returns number of logical cores, so
  # if you're using a hyperthreaded CPU, this will be more than the number of
  # physical cores you have.
  parallel = args.parallel if args.parallel is not None else multiprocessing.cpu_count()
  tree_chains = args.tree_chains if args.tree_chains is not None else parallel
  prior = {'garbage': 0.001}

  if args.seed is not None:
    np.random.seed(args.seed)
    random.seed(args.seed)

  variants = inputparser.load_ssms(args.ssm_fn)
  params = inputparser.load_params(args.params_fn)

  if os.path.exists(args.results_fn):
    results = resultserializer.load(args.results_fn)
  else:
    results = {}

  if 'mutrel_posterior' not in results:
    results['mutrel_posterior'], results['mutrel_evidence'] = pairwise.calc_posterior(variants, prior=prior, rel_type='variant', parallel=parallel)
    resultserializer.save(results, args.results_fn)

  if 'clustrel_posterior' not in results:
    if 'clusters' in params and 'garbage' in params:
      supervars, results['clustrel_posterior'], results['clustrel_evidence'], results['clusters'], results['garbage'] = clustermaker.use_pre_existing(
        variants,
        prior,
        parallel,
        params['clusters'],
        params['garbage'],
      )
    else:
      clustermaker._plot.prefix = os.path.basename(args.ssm_fn).split('.')[0]
      supervars, results['clustrel_posterior'], results['clustrel_evidence'], results['clusters'], results['garbage'] = clustermaker.cluster_and_discard_garbage(
        variants,
        results['mutrel_posterior'],
        results['mutrel_evidence'],
        prior,
        parallel,
      )
    resultserializer.save(results, args.results_fn)
  else:
    supervars = clustermaker.make_cluster_supervars(results['clusters'], variants)

  superclusters = clustermaker.make_superclusters(supervars)
  # Add empty initial cluster, which serves as tree root.
  superclusters.insert(0, [])

  if 'adjm' not in results:
    results['adjm'], results['llh'] = tree_sampler.sample_trees(
      results['clustrel_posterior'],
      supervars,
      superclusters,
      trees_per_chain = args.trees_per_chain,
      nchains = tree_chains,
      parallel = parallel,
    )
    resultserializer.save(results, args.results_fn)

  if 'phi' not in results:
    results['phi'], results['eta'] = fit_phis(
      results['adjm'],
      supervars,
      superclusters,
      tidxs = (-1,),
      iterations = args.phi_iterations,
      parallel = parallel,
    )
    resultserializer.save(results, args.results_fn)

if __name__ == '__main__':
  main()
