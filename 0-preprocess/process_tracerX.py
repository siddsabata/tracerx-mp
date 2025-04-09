import pandas as pd
import numpy as np
import argparse
import os
import sys
from pathlib import Path
import traceback

"""
The purpose of this script is to process mutation data from TRACERx data.

The script will process initial mutation data for patients, generating the SSM files
needed for phylogenetic analysis. Each patient will have an 'initial' directory for
this processed data, and an empty 'long' directory for future longitudinal analysis.

Results will be saved into the specified directory structure:
/PATIENT_ID/
    /initial/
        - ssm.txt
        - cnv.txt
        - [original data]
    /long/

You can run this script with the following command: 
python process_tracerX.py -i <input csv> -o <output directory> [-p <patient_id1,patient_id2,...>]
"""

def create_ssm_file(df, output_dir):
    """
    Creates SSM file from patient data and saves it to the output directory.
    
    Args:
        df (DataFrame): Patient data with mutation information
        output_dir (Path): Directory to save the SSM file
    
    Returns:
        int: Number of mutations processed
    """
    # Create unique identifiers for each mutation
    df['mutation_id'] = df.apply(
        lambda row: f"{row['Hugo_Symbol']}_{row['Chromosome']}_{row['Position']}_{row['Ref']}>{row['Mut']}", 
        axis=1
    )
    
    # Determine data format (2017 or 2023) based on column names
    is_2023_format = 'dao_t0' in df.columns and 'ddp_t0' in df.columns
    
    if is_2023_format:
        # 2023 format with variant reads and total reads
        required_columns = ['dao_t0', 'dao_t1', 'ddp_t0', 'ddp_t1']
        valid_mutations = df.dropna(subset=required_columns)
        print(f"Using 2023 data format with {len(valid_mutations)} mutations with complete data out of {len(df)} total")
    else:
        # 2017 format with VAF and depth of reference
        required_columns = ['PreOp_RefVAF', 'PostOp_RefVAF', 'PreOp_DOR', 'PostOp_DOR']
        valid_mutations = df.dropna(subset=required_columns)
        print(f"Using 2017 data format with {len(valid_mutations)} mutations with complete data out of {len(df)} total")
    
    ssm_entries = []
    # Process each mutation 
    for idx, row in enumerate(valid_mutations.iterrows()):
        _, mutation = row
        
        if is_2023_format:
            # 2023 format: Calculate reference reads by subtracting variant reads from total reads
            preop_total = mutation["ddp_t0"]
            preop_variant = mutation["dao_t0"]
            preop_ref = preop_total - preop_variant
            
            postop_total = mutation["ddp_t1"]
            postop_variant = mutation["dao_t1"]
            postop_ref = postop_total - postop_variant
        else:
            # 2017 format: Calculate reference reads from VAF and total depth
            preop_total = mutation["PreOp_DOR"]
            preop_ref = preop_total * mutation["PreOp_RefVAF"]
            
            postop_total = mutation["PostOp_DOR"]
            postop_ref = postop_total * mutation["PostOp_RefVAF"]
        
        # Format as comma-separated values
        ref_reads = f"{int(preop_ref)},{int(postop_ref)}"
        total_depth = f"{int(preop_total)},{int(postop_total)}"
        
        # Create unique identifier that includes the mutation details
        mutation_id = mutation['mutation_id']
        
        ssm_entries.append({
            "id": f"s{idx}",
            "gene": mutation_id,
            "a": ref_reads,        # reference reads as comma-separated list
            "d": total_depth,      # total depth as comma-separated list
            "mu_r": 0.999,
            "mu_v": 0.499
        })
    
    ssm_df = pd.DataFrame(ssm_entries)
    
    # Save SSM file
    ssm_file = output_dir / 'ssm.txt'
    ssm_df.to_csv(ssm_file, sep='\t', index=False)
    
    # Create empty CNV file (required by PhyloWGS)
    cnv_file = output_dir / 'cnv.txt'
    cnv_file.touch()
    
    return len(ssm_entries)  # Return number of mutations processed

def process_patient_data(patient_df, patient_id, output_dir):
    """
    Process initial data for a single patient and set up directory structure.
    
    Args:
        patient_df (DataFrame): Data for this patient
        patient_id (str): Patient identifier
        output_dir (Path): Base output directory
        
    Returns:
        bool: True if processing was successful
    """
    print(f"Processing data for patient {patient_id} with {len(patient_df)} mutations")
    
    # Create patient directory structure
    patient_dir = output_dir / patient_id
    initial_dir = patient_dir / 'initial'
    long_dir = patient_dir / 'long'
    
    os.makedirs(patient_dir, exist_ok=True)
    os.makedirs(initial_dir, exist_ok=True)
    os.makedirs(long_dir, exist_ok=True)
    
    # Save a copy of the original data
    patient_df.to_csv(initial_dir / f'{patient_id}_initial.csv', index=False)
    
    # Create SSM and CNV files
    mutation_count = create_ssm_file(patient_df, initial_dir)
    
    # Create a marker file in the long directory to indicate it's prepared but empty
    with open(long_dir / 'README.txt', 'w') as f:
        f.write(f"Directory prepared for future longitudinal analysis of patient {patient_id}.\n")
    
    print(f"Created SSM file with {mutation_count} mutations for patient {patient_id}")
    
    return True

def filter_patients_from_file(input_file, patient_ids=None):
    """
    Read input file and extract patient-specific data.
    
    Args:
        input_file (str): Path to input CSV file
        patient_ids (list, optional): List of patient IDs to include. If None, extract all.
        
    Returns:
        dict: Dictionary with patient IDs as keys and their mutation data as values
    """
    # Read the input file
    df = pd.read_csv(input_file)
    
    # Check if patient ID column exists
    if 'SampleID' not in df.columns and 'PatientID' not in df.columns:
        # If no patient ID column exists, extract patient ID from filename
        filename = Path(input_file).stem  # Get filename without extension
        patient_id = filename.split('_')[0]  # Extract patient ID (e.g., CRUK0044 from CRUK0044_init.csv)
        
        # If specific patient IDs requested, check if this file's patient is included
        if patient_ids and patient_id not in patient_ids:
            print(f"Skipping file for patient {patient_id} as it's not in the requested list")
            return {}
        
        return {patient_id: df}
    
    # If we have a patient ID column, extract data for each patient
    id_column = 'SampleID' if 'SampleID' in df.columns else 'PatientID'
    all_patient_ids = sorted(df[id_column].unique())
    
    # If no specific patients requested, use all
    if patient_ids is None:
        patient_ids = all_patient_ids
    
    # Check which requested patients exist in the data
    valid_patient_ids = [pid for pid in patient_ids if pid in all_patient_ids]
    
    if not valid_patient_ids:
        print("No valid patient IDs found in the data.")
        return {}
    
    # Extract data for each patient
    patient_data = {}
    for pid in valid_patient_ids:
        patient_data[pid] = df[df[id_column] == pid].copy()
        print(f"Found {len(patient_data[pid])} mutations for patient {pid}")
    
    return patient_data

def main():
    parser = argparse.ArgumentParser(description='Process TracerX mutation data for phylogenetic analysis')
    parser.add_argument('-i', '--input', required=True,
                       help='Input CSV file with mutation data')
    parser.add_argument('-o', '--output_dir', required=True,
                       help='Base output directory')
    parser.add_argument('-p', '--patients', 
                       help='Comma-separated list of patient IDs to process (if omitted, process all)')
    args = parser.parse_args()

    try:
        # Create output directory
        output_dir = Path(args.output_dir)
        os.makedirs(output_dir, exist_ok=True)
        
        # Parse patient IDs if provided
        patient_ids = None
        if args.patients:
            patient_ids = [pid.strip() for pid in args.patients.split(',')]
            print(f"Filtering to specified patients: {', '.join(patient_ids)}")
        
        # Read input file and extract patient data
        print(f"Reading input file: {args.input}")
        patient_data = filter_patients_from_file(args.input, patient_ids)
        
        if not patient_data:
            print("No patient data to process. Exiting.")
            return
        
        print(f"Found data for {len(patient_data)} patients")
        
        # Process each patient
        processed_patients = 0
        
        print("\n--- PROCESSING PATIENTS ---")
        for patient_id, df in patient_data.items():
            print(f"\nProcessing patient: {patient_id}")
            
            # Process patient data
            success = process_patient_data(df, patient_id, output_dir)
            if success:
                processed_patients += 1
                print(f"Successfully processed patient {patient_id}")
            else:
                print(f"Failed to process patient {patient_id}")
        
        print(f"\nCompleted processing {processed_patients} patients")
        
    except Exception as e:
        print(f"Error processing data: {str(e)}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()