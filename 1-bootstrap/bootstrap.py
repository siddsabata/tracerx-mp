import pandas as pd
import numpy as np
import os
import argparse
from pathlib import Path

"""
The purpose of this script is to perform bootstrapping on mutation data from TRACERx.

This script takes the processed initial data and performs bootstrapping to quantify
uncertainty in the variant calls. It creates multiple bootstrap replicates for both
the PreOp and PostOp samples, which can then be analyzed by PhyloWGS.

The bootstrapping process:
1. First resamples read depths while maintaining total coverage
2. Then resamples variant frequencies using the new depths
3. Repeats this process n times to create bootstrap replicates

Usage: 
python bootstrap.py -i <input csv file> -o <output directory> -n <number of bootstraps>
"""

def bootstrap_va_dt(AF_list, Depth_list, bootstrap_num):
    """
    Advanced bootstrapping of both depths and frequencies
    
    Args:
        AF_list: List of allele frequencies
        Depth_list: List of read depths
        bootstrap_num: Number of bootstrap samples
    
    Returns:
        Tuple of (bootstrapped frequencies, bootstrapped depths)
    """
    AF_array = np.array(AF_list)
    Depth_array = np.array(Depth_list)
    total_depth = sum(Depth_list)
    
    count = 0
    while True:
        count += 1
        new_Depth_list = np.random.multinomial(n=total_depth, 
                                             pvals=np.array(Depth_list)/total_depth, 
                                             size=bootstrap_num)
        
        if not np.any(new_Depth_list == 0):
            break
            
        if count >= 10:
            new_Depth_list[np.where(new_Depth_list == 0)] = 1
            break
    
    AF_list_update = np.zeros((len(AF_list), bootstrap_num))
    for i in range(len(AF_list)):
        for j in range(bootstrap_num):
            sample = np.random.binomial(n=new_Depth_list[j, i], 
                                      p=AF_list[i], 
                                      size=1)[0]
            AF_list_update[i, j] = sample / new_Depth_list[j, i]
    
    new_Depth_list = new_Depth_list.T
    return AF_list_update, new_Depth_list

def bootstrap_mutation_data(df, num_bootstraps):
    """
    Performs bootstrapping on mutation data with PreOp and PostOp samples
    
    Args:
        df: DataFrame containing mutation data with PreOp and PostOp columns
        num_bootstraps: Number of bootstrap iterations to perform
    
    Returns:
        DataFrame with original and bootstrapped columns
    """
    df_bootstrap = df.copy()
    
    # Process PreOp data
    preop_vaf = 1 - df["PreOp_RefVAF"].tolist()  # Convert RefVAF to variant VAF
    preop_depth = df["PreOp_DOR"].tolist()
    
    preop_vaf_boot, preop_depth_boot = bootstrap_va_dt(preop_vaf, preop_depth, num_bootstraps)
    
    # Create column names for bootstrapped results
    preop_vaf_cols = [f"PreOp_VAF_bootstrap_{i+1}" for i in range(preop_vaf_boot.shape[1])]
    preop_depth_cols = [f"PreOp_DOR_bootstrap_{i+1}" for i in range(preop_depth_boot.shape[1])]
    
    # Add bootstrapped PreOp columns
    df_bootstrap = pd.concat([
        df_bootstrap,
        pd.DataFrame(preop_vaf_boot, columns=preop_vaf_cols),
        pd.DataFrame(preop_depth_boot, columns=preop_depth_cols)
    ], axis=1)
    
    # Process PostOp data
    postop_vaf = 1 - df["PostOp_RefVAF"].tolist()  # Convert RefVAF to variant VAF
    postop_depth = df["PostOp_DOR"].tolist()
    
    postop_vaf_boot, postop_depth_boot = bootstrap_va_dt(postop_vaf, postop_depth, num_bootstraps)
    
    # Create column names for bootstrapped results
    postop_vaf_cols = [f"PostOp_VAF_bootstrap_{i+1}" for i in range(postop_vaf_boot.shape[1])]
    postop_depth_cols = [f"PostOp_DOR_bootstrap_{i+1}" for i in range(postop_depth_boot.shape[1])]
    
    # Add bootstrapped PostOp columns
    df_bootstrap = pd.concat([
        df_bootstrap,
        pd.DataFrame(postop_vaf_boot, columns=postop_vaf_cols),
        pd.DataFrame(postop_depth_boot, columns=postop_depth_cols)
    ], axis=1)
    
    return df_bootstrap

def write_bootstrap_ssm(bootstrap_df, bootstrap_num, output_dir):
    """
    Write SSM data for a specific bootstrap iteration
    
    Args:
        bootstrap_df: DataFrame with bootstrapped data
        bootstrap_num: The bootstrap iteration number
        output_dir: Directory to write the SSM files
    """
    # Create bootstrap directory
    bootstrap_dir = os.path.join(output_dir, f'bootstrap{bootstrap_num}')
    os.makedirs(bootstrap_dir, exist_ok=True)
    
    # Create SSM file paths
    ssm_file = os.path.join(bootstrap_dir, f'ssm_data_bootstrap{bootstrap_num}.txt')
    
    # Create phyloWGS input for this bootstrap iteration
    boot_phylowgs = []
    for idx, row in bootstrap_df.iterrows():
        # Create mutation identifier
        mutation_id = f"{row['Hugo_Symbol']}_{row['Chromosome']}_{row['Position']}_{row['Ref']}>{row['Mut']}"
        
        # Get PreOp values for this bootstrap
        preop_depth = int(row[f"PreOp_DOR_bootstrap_{bootstrap_num}"])
        preop_vaf = row[f"PreOp_VAF_bootstrap_{bootstrap_num}"]
        preop_ref = int(np.round(preop_depth * (1 - preop_vaf)))
        
        # Get PostOp values for this bootstrap
        postop_depth = int(row[f"PostOp_DOR_bootstrap_{bootstrap_num}"])
        postop_vaf = row[f"PostOp_VAF_bootstrap_{bootstrap_num}"]
        postop_ref = int(np.round(postop_depth * (1 - postop_vaf)))
        
        # Format as comma-separated values (PreOp first, then PostOp)
        ref_reads = f"{preop_ref},{postop_ref}"
        total_depth = f"{preop_depth},{postop_depth}"
        
        boot_phylowgs.append({
            'id': f's{idx}',
            'gene': mutation_id,
            'a': ref_reads,        # reference reads as comma-separated list
            'd': total_depth,      # total depth as comma-separated list
            'mu_r': 0.999,
            'mu_v': 0.499
        })
    
    # Save phyloWGS input for this bootstrap iteration
    df_boot = pd.DataFrame(boot_phylowgs)
    df_boot.to_csv(ssm_file, sep='\t', index=False)
    
    # Create empty CNV file (required by PhyloWGS)
    cnv_file = os.path.join(bootstrap_dir, f'cnv_data_bootstrap{bootstrap_num}.txt')
    open(cnv_file, 'w').close()  # Creates an empty file

def main():
    parser = argparse.ArgumentParser(description='Bootstrap mutation data')
    parser.add_argument('-i', '--input', required=True,
                       help='Input CSV file with mutation data')
    parser.add_argument('-o', '--output', required=True,
                       help='Output directory for bootstrapped files')
    parser.add_argument('-n', '--num_bootstraps', type=int, default=100,
                       help='Number of bootstrap iterations')
    args = parser.parse_args()

    # Ensure output directory exists
    os.makedirs(args.output, exist_ok=True)

    # Read input data
    print(f"Reading input file: {args.input}")
    df = pd.read_csv(args.input)
    
    # Perform bootstrapping
    print(f"Performing {args.num_bootstraps} bootstrap iterations...")
    bootstrap_df = bootstrap_mutation_data(df, args.num_bootstraps)
    
    # Save bootstrapped data
    bootstrap_df.to_csv(os.path.join(args.output, 'bootstrapped_mutations.csv'), index=False)

    # Create bootstrap SSM and CNV files
    print("Creating bootstrap files for PhyloWGS...")
    for i in range(1, args.num_bootstraps + 1):
        # Create SSM and CNV files for this bootstrap
        write_bootstrap_ssm(bootstrap_df, i, args.output)
    
    print(f"Bootstrap process completed. Files saved to {args.output}")

if __name__ == "__main__":
    main() 