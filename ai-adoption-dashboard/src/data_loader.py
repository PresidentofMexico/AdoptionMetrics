"""
Data Loader Module

This is the ONLY module that touches raw data (ETL logic).
All data loading and transformation happens here.
"""

import os
from typing import Optional
import pandas as pd


def load_raw_data(file_path: str) -> Optional[pd.DataFrame]:
    """
    Load raw CSV data from the data directory.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        DataFrame with loaded data or None if file doesn't exist
    """
    if not os.path.exists(file_path):
        return None
    
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        print(f"Error loading data from {file_path}: {e}")
        return None


def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply transformations to raw data.
    
    Args:
        df: Raw data DataFrame
        
    Returns:
        Transformed DataFrame
    """
    # Add transformation logic here
    return df
