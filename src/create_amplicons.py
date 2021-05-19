import subprocess
from os.path import join, basename
from io import StringIO
import pandas as pd


def build_index(genome_path, genome_filename_short, indices_folder):
    
    # create bowtie2 index for the reference
    subprocess.run([
        "bowtie2-build", genome_path, join(indices_folder, genome_filename_short)], stdout=subprocess.DEVNULL)

def align_primers(genome_path, genome_filename_short, indices_folder, primers_files, verbose):

    # run bowtie2 aligner
    alignment = subprocess.run(
        ["bowtie2", 
        "-x", join(indices_folder, genome_filename_short), 
        "-U", primers_files], capture_output=True)

    alignment = StringIO(alignment.stdout.decode("UTF-8"))
    
    # read alignment data as a dataframe
    df = pd.read_csv(alignment, sep="\t", skiprows=[0, 1, 2], header=None, error_bad_lines=False, warn_bad_lines=True, names=[i for i in range(19)])
    df = pd.DataFrame(df[[0, 2, 3, 9]])
    df = df.rename(columns={0:"name", 2:"ref", 3:"start", 9: "seq"})
    
    # split the column "name" to extract useful data
    df["seq_len"] = df["seq"].apply(len)
    df["amplicon_number"] = df["name"].apply(lambda x: int(x.split("_")[1]))
    df["handedness"] = df["name"].apply(lambda x: x.split("_")[2])
    df["is_alt"] = df["name"].apply(lambda x: len(x.split("_")) > 3)


    # remove rows where the alignment mismatched
    drop_rows = []        
    for r in df.itertuples():
        if r.ref == "*":
            if verbose:
                print(f"Dropping amplicon {r.amplicon_number}, couldn't find a match for the primer {r.seq}")

            drop_rows.append(r.Index)
    
    df.drop(drop_rows, inplace=True)
    
    # inner join the dataframe with itself, to get the pairs of primers and their start/end positions
    df = pd.merge(
        df.loc[df["handedness"] == "LEFT"], 
        df.loc[df["handedness"] == "RIGHT"], 
        on=["amplicon_number", "is_alt"]
    )

    # rename the columns to more understandable names
    df = pd.DataFrame(
        df[["ref_x", "amplicon_number", "is_alt", 
        "start_x", "seq_x", "seq_len_x", 
        "start_y", "seq_y", "seq_len_y"]]
    )

    df = df.rename(columns={
        "ref_x":"ref", 
        "start_x":"left", 
        "seq_x": "left_primer", 
        "seq_len_x":"left_primer_length", 
        "start_y":"right", 
        "seq_y": "right_primer", 
        "seq_len_y":"right_primer_length"})

    df["amplicon_filepath"] = genome_filename_short + "_amplicon_" + df["amplicon_number"].map(str) + df["is_alt"].map(lambda x: "_alt" if x else "") + ".fasta"


    if verbose:
        print("First 5 rows: ")
        print(df.head())

    return df


def write_amplicon(df, reference, genome_filename_short, amplicons_folder, verbose=False):

        for r in df.itertuples():
            amplicon_number = r.amplicon_number
            alt = r.is_alt
            reference_string = str(reference.seq)
            amplicon = reference_string[r.left - 1: r.right + r.right_primer_length - 1]
            
            if verbose:
                print(f">{reference.id}_amplicon_{amplicon_number}" + ("_alt" if alt else ""))
                print("length: " + str(r.right - r.left))
                print(amplicon + "\n")
                print(r.left_primer + "-"* (r.right - r.left - r.left_primer_length) + r.right_primer + "\n")     

            with open(f"{amplicons_folder}/{genome_filename_short}_amplicon_{amplicon_number}" + ("_alt" if alt else "") + ".fasta", "w") as f:

                f.write(f">{reference.id}_amplicon_{amplicon_number}" + ("_alt" if alt else "") + "\n")
                f.write(amplicon + "\n\n")