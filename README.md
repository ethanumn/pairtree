Pairtree
========
Pairtree infers the phylogeny underlying a cancer using genomic mutation data.
Pairtree is particularly suited to settings with multiple tissue samples from
each cancer, providing separate estimates of lineage frequency from each sample
that constrain the set of consistent phylogenies.  The Pairtree algorithm is
described in {insert link to paper}. The algorithm consists of two phases:

1. Compute pairwise relation tensor over all mutations (or clusters of
   mutations). This provides the probability over each of four possible
   evolutionary relationships between each pair of mutations `A` and `B`.

2. Use the pairwise relation tensor to sample possible phylogenies, assigning a
   likelihood to each. As each phylogeny is sampled, Pairtree computes the
   lineage frequency of each mutation (or cluster of mutations) within the
   tree, balancing the need to fit the observed mutation data while still
   obeying tree constraints.

Installing Pairtree
===================
1. Install dependencies. To ease installation, you may wish to use Anaconda
   {link}, which includes recent versions of Python 3, NumPy, and SciPy.

    * Python 3.6 or greater
    * NumPy
    * SciPy
    * tqdm (e.g., install via`pip3 install --user tqdm`)
    * C compiler (e.g., GCC)

2. Compile the C code required to fit lineage frequencies to the tree. This
   algorithm was published in {Jose paper}, and uses the authors'
   implementation with minor modifications.

    cd lib/freq_projection
    bash make.sh

3. Test your Pairtree installation.

    cd example/
    mkdir results && cd results
    # Run Pairtree.
    ../../bin/pairtree --params ../example.params.json ../example.ssm example.results.npz
    # Plot results in an HTML file.
    ../../bin/plotpairtree example ../example.ssm ../example.params.json example.results.npz example.results.html
    # View the HTML file.
    firefox example.results.html

Interpreting Pairtree output
============================
(add note about how logs will be written in JSON format if stdout/stderr is directed to a file)

Tweaking Pairtree options
=========================
Tweaking some of Pairtree's options can improve the quality of your results or
reduce the method's runtime. The most relevant options are discussed below.
For a full listing of tweakable Pairtree options, including algorithm
hyperparameters, run `pairtree --help`.

Finding better trees by running multiple MCMC chains
----------------------------------------------------
Pairtree samples trees using MCMC chains. Like any optimization algorithm
working with a non-convex objective, Pairtree's chains can become stuck in
local optima. Running multiple MCMC chains helps avoid this, since each chain
starts from a different point in space, and takes a different path through that
space.

By default, Pairtree will run a separate MCMC chain for each CPU core (logical
or physical) present. As these chains are run in parallel, using multiple
chains does not increase runtime. For more details, please refer to the
"Running computatins in parallel to reduce runtime" section below.

Changing number of samples, burn-in, and thinning
-------------------------------------------------
Three options control the behaviour of each MCMC chain used to sample trees.

* Number of MCMC samples: by changing the `--trees-per-chain` option, you can
  make each chain sample more or fewer trees. The more samples each chain
  takes, the more likely it is that those samples will be from a good
  approximation of the true posterior distribution over trees permitted by your
  data. By default, Pairtree will take 3000 total samples per chain.

* Burn-in: each chain will take some number of samples to reach high-density
  regions of tree space, such that those trees come from a good approximation
  of the true posterior. The `--burnin` paramemter controls what proportion of
  trees Pairtree will discard from the beginning of each chain, so as to avoid
  including poor-quality trees in your results. By default, Pairtree discards
  the first one-third of samples from each chain.

* Thinning: MCMC samples inherently exhibit auto-correlation, since each
  successive sample is based on a perturbation to the preceding one. We can
  reduce this effect by taking multiple samples for each one we record. You can
  change the `--thinned-frac` option to control this behaviour. By default,
  `--thinned-frac=1`, such that every sample taken is recorded. By changing
  this, for instance, to `--thinned-frac=0.1`, Pairtree will only record every
  tenth sample it takes. By recording only a subset of samples taken, the
  computational burden associated with processing the results (e.g., by
  computing summary statistics over the distribution of recorded trees) is
  reduced, alongside the storage burden of writing many samples to disk.


Running computations in parallel to reduce runtime
--------------------------------------------------
Pairtree can leverage multiple CPUs both when computing the pairwise relations
tensor and when sampling trees. Exploiting parallelism when computing the
tensor can drastically reduce Pairtree's runtime, since every pair can be
computed independently of every other. Conversely, exploiting parallelism when
sampling trees won't necessarily improve runtime, since trees are sampled using
MCMC, which is an inherently serial process, While no single MCMC chain can be
run in parallel, however, you can run multiple independent chains in parallel,
as discussed in the previous section. This will help Pairtree avoid local
optima and produce better-quality results.

By default, Pairtree will run in parallel on all present CPUs. (On
hyperthreaded systems, this number will usually be inferred to be twice the
number of physical CPU cores.) You can change this behaviour by specifying the
`--parallel=N` option, causing Pairtree to use `N` parallel processes instead.
When computing the pairwise tensor, Pairtree will compute all pairs in
parallel, such that computing the full tensor using `N` parallel processes
should only take `1/N` as much time as computing with a single process.  Later,
when sampling trees, Pairtree will by default run as many independent MCMC
chains as there are parallel processes. In this scenario, if you have `N` CPUs,
running only a single chain will be no faster than running `N` chains, since
each chain executes concurrently. However, in the `N`-chain case, you will
obtain `N` times as many samples, improving your result quality.

You can explicitly specify `--tree-chains=M` to run `M` chains instead of the
default, which is to run a separate chain for each parallel process. If `M` is
greater than the number of parallel processes `N`, the chains will execute
serially, increasing runtime. (Given the serial execution, you should expect
that tree sampling with `M > N` will take `ceiling(M / N)` times as long as
sampling with `M = N`.)

Using alternative algorithms to fit lineage frequencies to each tree
--------------------------------------------------------------------
