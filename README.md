Pairtree
========
Pairtree infers the phylogeny underlying a cancer using genomic mutation data.
Pairtree is particularly suited to settings with multiple tissue samples from
each cancer, providing separate estimates of subclone frequency from each sample
that constrain the set of consistent phylogenies.  The Pairtree algorithm is
described in {insert link to paper}. The algorithm consists of two phases:

1. Compute pairwise relation tensor over all mutations (or clusters of
   mutations). This provides the probability over each of four possible
   evolutionary relationships between each pair of mutations `A` and `B`.

2. Use the pairwise relation tensor to sample possible phylogenies, assigning a
   likelihood to each. As each phylogeny is sampled, Pairtree computes the
   subclone frequency of each mutation (or cluster of mutations) within the
   tree, balancing the need to fit the observed mutation data while still
   obeying tree constraints.

The algorithm is described in [Reconstructing complex cancer evolutionary
histories from multiple bulk DNA samples using
Pairtree](https://doi.org/10.1101/2020.11.06.372219) (Wintersinger et al.
(2021)).


Installing Pairtree
===================
1. Install dependencies. Installation is usually easiest if you use
   [Anaconda](https://www.anaconda.com/products/individual), which includes the
   most difficult-to-install dependencies.
   [Miniconda](https://docs.conda.io/en/latest/miniconda.html) also works well.
   You need the following:

    * [Python](https://www.python.org/) 3.6 or greater **(included in Anaconda)**
    * [NumPy](https://numpy.org/) **(included in Anaconda)**
    * [SciPy](https://www.scipy.org/) **(included in Anaconda)**
    * [scikit-learn](https://scikit-learn.org/stable/) **(included in Anaconda)**
    * [tqdm](https://github.com/tqdm/tqdm) (e.g., install via `pip3 install --user tqdm`) **(included in Anaconda)**
    * [Numba](https://numba.pydata.org/) (e.g., install via `pip3 install --user numba` or `conda install numba`)
    * [colorlover](https://github.com/plotly/colorlover) (e.g., install via `pip3 install --user colorlover`)
    * C compiler (e.g., GCC)

   Pairtree has only been tested on Linux systems, but should work on any
   UNIX-like OS (including macOS).

2. Clone the Pairtree repository, then download and build the C code required
   to fit subclone frequencies to the tree. This algorithm was published in
   [Jia et al.](https://arxiv.org/abs/1811.01129), and uses the authors' implementation with minor modifications.

        git clone https://github.com/jwintersinger/pairtree
        cd pairtree/lib
        git clone https://github.com/jwintersinger/projectppm
        cd projectppm
        bash make.sh


Test your Pairtree installation
===============================
After installing Pairtree, you can test your installation using provided
example data.

        PTDIR=$HOME/path/to/pairtree
        cd $PTDIR/example
        mkdir results && cd results
        # Run Pairtree.
        $PTDIR/bin/pairtree --params $PTDIR/example/example.params.json $PTDIR/example/example.ssm example.results.npz
        # Plot results in an HTML file.
        $PTDIR/bin/plottree --runid example $PTDIR/example/example.ssm $PTDIR/example/example.params.json example.results.npz example.results.html
        # View the HTML file.
        firefox example.results.html


Pairtree executables
====================
Pairtree provides several executable files to be used at different stages of
your clone-tree-building pipeline. You can run each executable with the
`--help` flag to get full usage instructions.

* `bin/clustervars`: cluster variants into subclones suitable for building
  clone trees with `bin/pairtree`. Please see the [Clustering
  mutations](#clustering-mutations) section for full instructions.

* `bin/plotvars`: plot information about your variant clusters before
  proceeding with your Pairtree run. This step is optional. If
  `--plot-relations` is specified, the pairwise relations between subclones
  will be computed and plotted, but at a considerable computational cost.

* `bin/pairtree`: the main Pairtree executable, used for building clone trees.
  See the [Input files](#input-files) and [Tweaking Pairtree
  options](#tweaking-pairtree-options) sections for more information specific
  to this step.

* `bin/plottree`: plot results of your Pairtree run. This will plot a single
  clone tree, which by default will be the one with highest likelihood. See
  [Interpreting Pairtree output](#interpreting-pairtree-output) for details.

* `bin/summposterior`: summarize the posterior distribution over clone trees
  from your Pairtree run by representing this distribution as a graph, and by
  showing the best individual tree samples. See [Interpreting Pairtree
  output](#interpreting-pairtree-output) for details.


Input files
===========
Pairtree requires two input files.

SSM file
---------
Pairtree needs a `.ssm` (i.e., simple somatic mutation) file, which provides
integer counts of the number of variant and total reads at each mutation locus
in each tissue sample. The `.ssm` file is tab-delimited, with the first line
serving as a header, and each subsequent line providing data for one mutation.
You may wish to consult [an example .ssm file](example/example.ssm).

The `.ssm` file contains the following fields:

  * `id`: a unique ID used to identify the variant. The first mutation should
    be assigned ID `s0`, with subsequent variants assigned `s1, s2, ...`.
    Generally, these should be contiguous, but this is not enforced, so you
    should be able to delete variants from this file without adjusting
    subsequent IDs. The `s` prefix indicates that the ID corresponds to an
    SSM.

  * `name`: a text string used to label variants in Pairtree's output. This
    can be a gene name, genome position (e.g., `1_12345` may be used to
    represent that the variant occurred on `chr1` at position `12345`), or any
    other string. Spaces may be used, and uniqueness of `name`s is not
    enforced (though duplicate names may lead to confusing output).

  * `var_reads`: a comma-separated vector of how many whole-number-valued
    genomic reads at this mutation's locus corresponded to the variant allele
    in each tissue sample. Tissue samples may be provided in any order, so long
    as this order is consistent for all mutations. The names of the associated
    tissue samples are given in the `.params.json` file, detailed below. If
    running with only a single tissue sample, this field contains only a single
    scalar value for each mutation. If a variant has been called in only a
    subset of your tissue samples, consult the [Imputing read
    counts](#imputing-read-counts-for-mutations-missing-in-some-samples)
    section.

  * `total_reads`: a comma-separated vector of the total number of
    whole-number-valued genomic reads observed at this mutation's locus in each
    tissue sample. Thus, the variant allele frequency (VAF) is given by
    `var_reads / total_reads`. If a variant has been called in only a subset of
    your tissue samples, consult the [Imputing read
    counts](#imputing-read-counts-for-mutations-missing-in-some-samples)
    section.

  * `var_read_prob`: a comma-separted vector of probabilities `\omega_{j1},
    \omega_{j2}, ..., \omega_{js}, ..., \omega_{jS}`, where `S` is the total
    number of tissue samples. The value `\omega_{js}` indicates the probabilty
    of observing a read from the variant allele for mutation `j` in a cell
    bearing the mutation. Thus, if mutation `j` occurred at a diploid locus,
    we should have `\omega_{js} = 0.5`. In a haploid cell (e.g., male sex
    chromosome), we should have `\omega_{js} = 1.0`. If a copy-number
    aberration (CNA) duplicated the reference allele in the lineage bearing
    mutation `j` prior to `j` occurring, there will be two reference alleles
    and a single variant allele in all cells bearing `j`, such that
    `\omega_{js} = 0.3333`. Thus, these values give Pairtree the ability to
    correct for the effect CNAs have on the relationship between VAF (i.e.,
    the proportion of alleles bearing the mutation) and subclonal frequency
    (i.e., the proportion of cells bearing the mutation).

Parameters file
---------------
Pairtree also needs a `.params.json` file, which provides parameters for the Pairtree run.
You may wish to consult [an example .params.json file](example/example.params.json).

The `.params.json` file denotes three objects:

* `samples` (required): list of sample names, provided in the same order as
  entries in the `var_reads` and `total_reads` vectors in the `.ssm` file. Each
  sample name can be an arbitrary string.

* `clusters` (required): list-of-lists denoting variant clusters, each of which
  corresponds to a subclone. Each sub-list contains strings corresponding to
  the IDs of all variants that belong to a given cluster. All variants
  belonging to a cluster are assumed to share the same subclonal frequency in a
  given tissue sample, with the VAFs of each variant serving as a noisy
  estimate of this subclonal frequency after using `var_read_prob` to correct
  for ploidy. See the [section on clustering mutations](#clustering-mutations)
  for instructions on how to use Pairtree to build clusters. Pairtree assumes
  that all variants within a cluster share the same subclonal frequencies
  across all cancer samples. Ploidy-corrected estimates of these frequencies
  can be obtained by dividing a variant's VAF by its variant read probability
  `omega.

* `garbage` (optional): list of IDs in the `.ssm` file that you do not want
  Pairtree to use in building your clone tree. Specifying variants as `garbage`
  can be useful when you want to exclude variants without having to remove them
  from the `.ssm` file, allowing you to easily re-introduce them to your clone
  tree in the future. Typically, you might remove a variant because you've
  determined that it violates the infinite sites assumption (ISA); because you
  think the associated read count data is likely erroneous; or because the
  variant was subject to a complex copy-number configuration that skews the
  relationship between VAF and subclonal frequency (e.g., the variant appears
  in different copy-number states in different subclones).


Imputing read counts for mutations missing in some samples
==========================================================
When some of your mutations appear in only some of your samples, you must
impute the total read count for those mutations in the samples where they're
not present. While the variant read count should clearly be zero in such cases,
the value the total read count should take is unclear. This task is important,
however, because it informs Pairtree how confident you are that the variant is
indeed not present in the sample -- an instance where you have zero variant
reads amongst ten total reads indicates considerably less confidence than if
you have zero variant reads for 1000 total reads.

To impute missing read counts, you ahve three options.


Clustering mutations
====================
Pairtree requires mutations be clustered into subclones. These clusters should
be provided to Pairtree in the `.params.json` file using the `clusters` array,
described above. Pairtree works best with thirty or fewer subclones, but can
build (less accurate) clone trees for 100 subclones or more.

To build clusters, you have three options.

1. Don't actually cluster mutations into subclones. That is, instead of
   building a *clone tree*, you can build  a  *mutation tree* instead in which
   each cluster contains only a single variant. You must still specify the
   clusters in your `.params.json` file, but you simply list a separate cluster
   for each variant. This works best for a small number of mutations (30 or
   fewer), and so is most suitable for sequencing data obtained from WES or
   targetted sequencing rather than WGS.

2. Use one of many published clustering methods, such as
   [PyClone-VI](https://bmcbioinformatics.biomedcentral.com/articles/10.1186/s12859-020-03919-2).
   You must translate these methods' outputs into Pairtree's format, but this
   is typically easy.

3. Use Pairtree to cluster the variants.

Pairtree provides two clustering models. As Pairtree's focus is not on variant
clustering, its clustering algorithms are less well-validated than its tree
building, and so you may obtain better results with other algorithms.
Nevertheless, Pairtree's authors have had reasonably good success with its
cluster-building methods. Pairtree's two clustering models both use a Dirichlet
process mixture model (DPMM), but differ in how they use the model.

You can use Pairtree to cluster variants through the `bin/clustervars`
executable. Run with `--help` to obtain full usage instructions. Several
options are of particular interest.

* `--model linfreq`: This uses the default "lineage frequency" clustering model.
  This is the most computationally efficient choice, and is the most
  straightforwrd application of the DPMM to the clustering problem.

* `--model pairwise`: This uses the alternative "pairwise relationships"
  clustering model. In some instances, it may produce better results than
  `linfreq`. This model is typically slower to use, as it requires computing
  pairwise relationships between mutation pairs. For `M` mutations, there are
  `(M choose 2)` such pairs, and so this may become frustratingly slow for more
  than 1000 mutations.

* `--prior <value>`. This is used only with `--model pairwise`. This option
  specifies the prior probability for the coclustering relationship. The
  default of `0.25` corresponds to a uniform relationship over the four
  relationship types (i.e., coclustering, `A` is ancestral to `B`, `B` is
  ancestral to `A`, and `A` and `B` are on different branches). Higher values
  typically result in fewer, larger clusters. Valid values range between 0 and 1.

* `--concentraton <value>`. This is the `log_10{alpha}` used in the DPMM.
  Larger values typically result in more, smaller clusters.

Clustering results are sensitive to the model and parameters used. The best
choice of parameters depends on the nature of your data, including the number
of variants, read depth, and other characteristics. It is often prudent to try
a range of different parameters, plot the results for each using the
`bin/plotvars` executable, and select the clustering that best represents your
data. The best clustering can depend on your application -- for some uses, you
may want more granular clusters that produce a detailed tree with many
subclones, while in other uses, you may want to collapse together similar
subclones to create a simpler tree in which it is easier to discern major
structural differences.


Interpreting Pairtree output
============================
* To export Pairtree's visualizations from `bin/plottree` for use in
  publications, try [SVG Crowbar](https://nytimes.github.io/svg-crowbar/). All
  figures Pairtree creates are in SVG format, which is suitable for use at
  arbitrarily high resolutions (including in print) because of its vector-based
  nature.
* (add note about how logs will be written in JSON format if stdout/stderr is directed to a file)
* (add note about summposterior, plottree, etc.)


Fixing incorrect ploidy
==========================
There are cases of incorrect ploidy that are unable to be detected using the pairwise framework.
This can result in an implied subclonal frequency being greater than 1. This is often due to missed
copy number calls, such as an uncalled loss of heterozygosity (LOH) event which removes the wildtype
allele in a lineage and leaves only the variant allele.

In order to find these mutations such that they can be corrected, we provide the script fix_bad_var_read_prob.py
that can be found in the /util directory. Several options are of particular interest.

* `--logbf-threshold`: Logarithm of Bayes factor threshold at which the haploid model is accepted as more likely model than the model using the provided var_read_prob.
* `--ignore-existing-garbage`: Ignore any existing garbage variants listed in in_params_fn and test all variants. If not specified, any existing garbage variants will be kept as garbage and not tested again.
* `--action (add_to_garbage, modify_var_read_prob)`: Action to take after script has completed. `add_to_garbage` will add the resulting bad_ssms to the list of garbage samples in the params.json file provided. `modify_var_read_prob` will overwrite the var_read_prob in the params.json file with the value provided by the `--var-read-prob-alt` option of this script.
* `--var-read-prob-alt`: Value that will be used to overwrite the var_read_prob of any garbage variants found if `--action` is set to `modify_var_read_prob`.
* `in_ssm_fn`: Input SSM file with mutations.
* `in_params_fn`: Input params file listing sample names and any existing garbage mutations.
* `out_ssm_fn`: Output SSM file with modified list of garbage mutations.
* `out_params_fn`: Output params file with modified list of garbage mutations.


The terminal output of this script will be in the following format:

`num_bad_ssms`: Number of variants which have an incorrect variant read probability estimate

`bad_ssms`: List of variant names which were found to have an incorrect variant read probability estimate


`bad_samp_prop`: Percent of variants out of all samples which were found to have an incorrect variant read probability estimate


`bad_ssm_prop`: Percent of variants which were found to have an incorrect variant read probability estimate in at least one sample


<br>


Removing garbage mutations
==========================
Pairtree relies on the infinite sites assumption (ISA) when converting mutation allele frequencies to subclonal frequencies, and building clone trees. Pairtree is also sensitive to other factors such as missed CNA calls, or technical noise which can skew the subcloncal frequency conversion. Therefore, it is necessary to detect and remove such mutations before building the clone tree. Pairwise relationships between mutations reveal both ISA violations and other types of erroneous mutations, which we refer to collectively as _garbage mutations_.

In order to find these mutations such that they can be corrected, we provide the script removegarbage
that can be found in the /bin directory. There are several options for this script which are of particular interest.

* `--prior`: Pairwise garbage prior probability. The default value of 0.2 represents a uniform prior over pairwise relationship types.
* `--max-garb-prob`: Maximum probability of garbage to permit for any pair when the algorithm terminates.
* `--ignore-existing-garbage`: Ignore any existing garbage variants listed in in_params_fn and test all variants. If not specified, any existing garbage variants will be kept as garbage and not tested again
* `--pairwise-results`: Filename to store pairwise evidence in, which allows you to try garbage removal with different parameters without having to repeat the pairwise computations.
* `in_ssm_fn`: Input SSM file with mutations.
* `in_params_fn`: Input params file listing sample names and any existing garbage mutations.
* `out_params_fn`: Output params file with modified list of garbage mutations.



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

Fitting subclone frequencies to trees
-------------------------------------
Critical to the Pairtree algorithm is the step of fitting subclone frequencies
to trees. Beyond the user's interpretation of subclone frequencies for
downstream analysis of Pairtree's results, the subclone frequencies will also
affect tree structure -- the data likelihood for a tree is determined by how
well the tree-constrained subclone frequencies fit the observed VAF data. We
provide several different algorithms for computing these frequencies that
strike different balances between computational speed and result accuracy.

* `--phi-fitter=projection`: By default, Pairtree uses the "Efficient
  Projection onto the Perfect Phylogeny Model" algorithm developed in [Jia et
  al.](https://arxiv.org/abs/1811.01129) This uses a Gaussian approximation of
  the binomial likelihood we're trying to maximize.

* `--phi-fitter=rprop`: Uses the [rprop variant of gradient
  descent](https://ieeexplore.ieee.org/document/298623). Separate step sizes
  are maintained for each frequency scalar in each tissue sample. Those step
  sizes are increased when the direction of a step is consistent with the
  previous step taken, and reduced otherwise. Generally, this algorithm will
  produce more accurate results than `projection` (i.e., higher data
  likelihoods for the same tree), since it is directly optimizing the binomial
  objective rather than a Gaussian approximation, but at a higher computational
  cost. The extra computational burden becomes greater with more subclones
  (e.g., 30 or more), while being insignificant for small trees (e.g., with ten
  subclones or fewer).

* `--phi-fitter=proj_rprop`: First run the default `projection` algorithm, then refine its
  results using `rprop`. While this can produce better subclone frequency values
  at the cost of more computation, it has in testing demonstrated little
  benefit to accuracy.

Given the tradeoff between speed and accuracy, `rprop` is recommended for small
trees (e.g., ten subclones or fewer), while `projection` is more suitable for
larger trees. If Pairtree seems to be producing poor results with `projection`,
try with `rprop` instead, as optimizing the exact objective rather than an
approximation may produce better trees.

When running with `--phi-fitter=rprop` or `--phi-fitter=proj_rprop`, you can
adjust the number of iterations the `rprop` algorithm uses by specifying the
`--phi-iterations=N` parameter. Runtime of `rprop` will be proportional to this
parameter, so smaller values will decrease runtime, at the potential cost of
accuracy of subclone frequencies.

While other options are provided (`--phi-fitter=graddesc_old` and
`--phi-fitter=rprop_old`), these remain only as artifacts and will be removed
in future verisons, and so should not be used.
