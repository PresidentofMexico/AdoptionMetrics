"""
Data Processor Module - The ETL Engine

This module normalizes ChatGPT and BF (Business Function) export data.
Handles data loading, cleaning, and transformation.
"""

import os
from typing import Optional, Dict, Any
import pandas as pd
from src.config import DATA_DIR, CHATGPT_EXPORT_FILENAME, BF_EXPORT_FILENAME


def load_chatgpt_data(data_dir: str = DATA_DIR) -> Optional[pd.DataFrame]:
    """
    Load and normalize ChatGPT export data.
    
    Args:
        data_dir: Directory containing data files
        
    Returns:
        Normalized DataFrame or None if file doesn't exist
    """
    file_path = os.path.join(data_dir, CHATGPT_EXPORT_FILENAME)
    
    if not os.path.exists(file_path):
        return None
    
    try:
        df = pd.read_csv(file_path)
        # Add normalization logic here
        return df
    except Exception as e:
        print(f"Error loading ChatGPT data from {file_path}: {e}")
        return None


def load_bf_data(data_dir: str = DATA_DIR) -> Optional[pd.DataFrame]:
    """
    Load and normalize BF (Business Function) export data.
    
    Args:
        data_dir: Directory containing data files
        
    Returns:
        Normalized DataFrame or None if file doesn't exist
    """
    file_path = os.path.join(data_dir, BF_EXPORT_FILENAME)
    
    if not os.path.exists(file_path):
        return None
    
    try:
        df = pd.read_csv(file_path)
        # Add normalization logic here
        return df
    except Exception as e:
        print(f"Error loading BF data from {file_path}: {e}")
        return None


def normalize_user_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize user data from different sources to a common format.
    
    Args:
        df: Raw data DataFrame
        
    Returns:
        Normalized DataFrame with consistent column names and formats
    """
    # Placeholder for normalization logic
    # This will standardize column names, data types, and formats
    return df


def merge_data_sources(chatgpt_df: Optional[pd.DataFrame], 
                       bf_df: Optional[pd.DataFrame]) -> pd.DataFrame:
    """
    Merge ChatGPT and BF data sources into a unified dataset.
    
    Args:
        chatgpt_df: ChatGPT export DataFrame
        bf_df: BF export DataFrame
        
    Returns:
        Merged and deduplicated DataFrame
    """
    dataframes = []
    
    if chatgpt_df is not None and not chatgpt_df.empty:
        dataframes.append(chatgpt_df)
    
    if bf_df is not None and not bf_df.empty:
        dataframes.append(bf_df)
    
    if not dataframes:
        return pd.DataFrame()
    
    # Merge dataframes
    merged_df = pd.concat(dataframes, ignore_index=True)
    
    # Remove duplicates if any
    # Add deduplication logic based on user ID or email
    
    return merged_df
