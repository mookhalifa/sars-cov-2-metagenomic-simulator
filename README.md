# SWAMPy

This project is intended to simulate SARS-CoV-2 metagenomes taken from wastewater samples. Synthetic mixtures of amplicons are produced, based on proportions of viral genomes that are supplied by the user and a supported primer set of choice. See [our method](https://github.com/goldman-gp-ebi/sars-cov-2-metagenomic-simulator/wiki/SWAMPy-method) to learn about how it works.


![image](https://user-images.githubusercontent.com/57137586/151800373-55048f9a-3f34-42f3-9f63-8f6190c5bde4.png)



## Installation

1. Clone this repository. 

```
git clone https://github.com/goldman-gp-ebi/sars-cov-2-metagenomic-simulator.git

cd sars-cov-2-metagenomic-simulator
```
2. Install dependencies `pandas` and `biopython`.
You need to ensure `bowtie2` and `art_illumina` are available from your command line (i.e. both of the binaries of these tools are available from your `$PATH` environment variable). The program also requires Python version 3.9.7.

A way to do this on a Debian-based system, with Python 3.9.7 and pip already installed, is below: 

```
pip install pandas, biopython
sudo apt-get install art_illumina, bowtie2
```

Or you can also use conda as follows to create a new environment with the dependencies and correct versions (RECOMMENDED):

```
conda env create -f SWAMPy-env.yaml
conda activate SWAMPy
```

**MAC USERS** also need:
```
brew install coreutils
```

## Quickstart

Example [input files](https://github.com/goldman-gp-ebi/sars-cov-2-metagenomic-simulator/wiki/SWAMPy-method#1-read-input-files) i.e. genomes.fasta and abudances.tsv are already included in the example directory.

### Run the example simulation

This creates a synthetic metagenome from the fasta files in the example/genomes folder, using relative genome proportions from the example/abundances.tsv. The primers used are from the ARTIC protocol v1; compared to v3, the primers marked as 'alt' are removed. For details, please see the potential bugs section below.

### Run the simulator with default parameters
```
cd src
```

```
python simulate_metagenome.py --genomes_file ../example/genomes.fasta --genome_abundances ../example/abundances.tsv --output_folder ../simulation_output --temp_folder ../example/temp/ --autoremove
```

### See the help page 
```
python simulate_metagenome.py --help
```

### Run the same example simulation again with all the parameters explicitly defined, and with the random seed set. 
```
python simulate_metagenome.py \
    --genomes_file ../example/genome.fasta \
    --temp_folder ../example/temp/ \
    --genome_abundances ../example/abundances.tsv \
    --primer_set a1 \
    --output_folder ../simulation_output \
    --output_filename_prefix example \
    --n_reads  100000 \
    --seqSys MSv3 \
    --read_length 250 \
    --seed 10 \
    --amplicon_distribution  dirichlet_1 \
    --amplicon_pseudocounts 10000 \
    --unique_insertion_rate 0.00002 \
    --unique_deletion_rate 0.000115 \
    --unique_substitution_rate 0.002485 \
    --recurrent_insertion_rate 0.00002 \
    --recurrent_deletion_rate 0 \
    --recurrent_substitution_rate 0.003357 \
    --max_insertion_length 14 \
    --subs_VAF_alpha 0.36,0.27 \
    --del_VAF_alpha 0.59,0.42 \
    --ins_VAF_alpha 0.33,0.45 \
    --r_subs_VAF_alpha 0.36,0.27 \
    --r_del_VAF_alpha 0.59,0.42 \
    --r_ins_VAF_alpha 0.33,0.45 
```
example1.fastq and example2.fastq should appear in simulation_output folder, as well as example_amplicon_abundances_summary.tsv, example.log and example_PCR_erros.vcf. While running, some tmp files might appear in your working directory, but they will get cleaned up when the program terminates (even if it exits with an error).

## Output files:
- example_R1.fastq & example_R2.fastq: simulated reads.
- example_amplicon_abundances_summary.tsv: a table summarising the amplicons.
- example_PCR_erros.vcf: all the intended high-frequency errors. Observed VAFs may be different from those in the VCF file due to randomness and recurrence.
- example.log: The log file.

## What these CLI arguments mean:

See the [CLI arguments](https://github.com/goldman-gp-ebi/sars-cov-2-metagenomic-simulator/wiki/CLI-arguments) page.

## Extra options and potential bugs

Things to watch out for:

- If you want to run multiple instances of SWAMPy simultaneously, make sure to use a unique `--TEMP_FOLDER` for each run. Otherwise, they will interfere with each other. Submitting multiple SLURM or LSF jobs or using SWAMPy in a Snakemake rule are examples of situations where this warning may apply. 

- First and last amplicons get dropped for basically every genome except the Wuhan reference.
This is because the leftmost primer 1 and rightmost primer 98 basically never match in a genome. 
Also watch out for long runs of N's in the primer sites, if these are there then that amplicon will drop out. 

- Special characters in the fasta genome ids could potentially cause a problem. In the code, the characters "/", "," and " " are dealt with,
but other whitespace characters or special characters such as "&" could cause a bug. 

- Note that the reads in the fastq files are both shuffled by a randomly chosen permutation. 

- The option 'dirichlet_1' relates to how numbers of reads for each genome and for each amplicon are drawn. At the moment
this is done using multiple Multinomial(N_genome, p) draws, where p is drawn once from a Dirichlet(\alpha * c) distribution. 
Here c is a scalar, the amplicon_pseudocounts number, and \alpha is a vector, scaled to have length 1, goverened by the amplicon_distribution file. N_genome is the number of reads for each genome, this is taken from the genome_abundances file. In the future, slightly different methods
of taking these draws may be possible, so this method is called 'dirichlet_1'. 

- Alt primers are only really relevant to **ARTIC v3**. ARTIC v3 has extra primers which are tagged as ALT - these are 'alternative' primer ends for certain amplicons where the original amplicons were dropping out a lot. These 'alt' primers are added to the primer pool along with the original primers. Therefore for these amplicons (where alt primers exist), there are a total of four possible versions of the amplicon that could be made, depending on whether the left/right end was used with the alt primer or not. In the original version of this code, we would only simulate two of these possibilities --- cases where both ends used the original primer and cases where both ends used the alt primer. However since then, because ARTIC v4 (which we assume will end up superceding ARTIC v3) was released, and has no alts (and also most other sequencing protocols have no alts either) we decided to ignore alt primers altogether, and our version of ARTIC does not include any simulation of alt primers. If you want this feature please contact us.

## Aknowledgements

We are using [bowtie2](http://bowtie-bio.sourceforge.net/bowtie2/index.shtml), [ART](https://www.niehs.nih.gov/research/resources/software/biostatistics/art/index.cfm) and [biopython](https://biopython.org/), as well as other python packages (pandas and numpy)
and are using a primer set coming from [ARTIC v1](https://artic.network/). 
The genomes in the example are courtesy of [Twist Bioscience](https://www.twistbioscience.com/); these genomes are in turn copies of surveillance sequences from [COG UK](https://www.cogconsortium.uk/). 


---
associated repos:
[Will's notes](https://github.com/goldman-gp-ebi/wastewater_Will-s_notes.git)
