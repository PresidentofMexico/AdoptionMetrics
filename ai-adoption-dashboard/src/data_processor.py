import pandas as pd
import glob
import os
import re
import streamlit as st
from . import config

class DataProcessor:
    def __init__(self):
        # Safely handle config if DATA_DIR is missing
        self.data_dir = getattr(config, 'DATA_DIR', 'data')
        self.month_map = {
            'January': 1, 'February': 2, 'March': 3, 'April': 4, 'May': 5, 'June': 6,
            'July': 7, 'August': 8, 'September': 9, 'October': 10, 'November': 11, 'December': 12
        }

    def get_date_from_filename(self, filename):
        """
        Extracts date from filenames. 
        Returns a timestamp defaulting to current time if not found.
        """
        base_name = os.path.basename(filename)
        
        # 1. Try finding full month name (e.g., "October")
        for month_name, month_num in self.month_map.items():
            if month_name in base_name:
                # Infer year: look for 4 digits, otherwise default to 2025
                year = 2025
                year_match = re.search(r'202\d', base_name)
                if year_match:
                    year = int(year_match.group(0))
                
                return pd.Timestamp(year=year, month=month_num, day=1)
        
        # 2. Fallback
        return pd.Timestamp.now()

    def load_openai_data(self):
        """Loads all OpenAI files matching the glob pattern."""
        pattern = getattr(config, 'OPENAI_GLOB_PATTERN', '*openai*.csv')
        all_files = glob.glob(os.path.join(self.data_dir, pattern))
        df_list = []
        
        for filename in all_files:
            try:
                df = pd.read_csv(filename)
                # Normalize columns
                df.columns = [c.lower().replace(' ', '_') for c in df.columns]
                
                # Add metadata
                report_date = self.get_date_from_filename(filename)
                df['report_date'] = report_date
                df['month'] = report_date.strftime('%Y-%m')
                df['tool'] = 'OpenAI'
                
                # Standardize Email
                if 'user_email' not in df.columns and 'email' in df.columns:
                    df['user_email'] = df['email']
                
                df_list.append(df)
            except Exception as e:
                print(f"Error loading OpenAI file {filename}: {e}")
                continue
                
        return pd.concat(df_list, ignore_index=True) if df_list else pd.DataFrame()

    def load_blueflame_data(self):
        """Loads all BlueFlame files matching the glob pattern."""
        pattern = getattr(config, 'BLUEFLAME_GLOB_PATTERN', '*blueflame*.csv')
        all_files = glob.glob(os.path.join(self.data_dir, pattern))
        df_list = []
        
        for filename in all_files:
            try:
                df = pd.read_csv(filename)
                df.columns = [c.lower().replace(' ', '_') for c in df.columns]
                
                report_date = self.get_date_from_filename(filename)
                df['report_date'] = report_date
                df['month'] = report_date.strftime('%Y-%m')
                df['tool'] = 'BlueFlame'
                
                df_list.append(df)
            except Exception as e:
                print(f"Error loading BlueFlame file {filename}: {e}")
        
        return pd.concat(df_list, ignore_index=True) if df_list else pd.DataFrame()

# ---------------------------------------------------------
# MASTER FUNCTION: Called by Home.py
# ---------------------------------------------------------
@st.cache_data
def load_and_process_data():
    """
    Loads all data sources, merges them, and prepares the final
    dataframe for visualization.
    Returns: (combined_df, total_users, total_vol)
    """
    processor = DataProcessor()
    
    # 1. Load raw data
    openai_df = processor.load_openai_data()
    blueflame_df = processor.load_blueflame_data()
    
    # 2. Combine
    combined_df = pd.concat([openai_df, blueflame_df], ignore_index=True)

    if combined_df.empty:
        return pd.DataFrame(), 0, 0

    # 3. Standardize Columns for Home.py
    # Create 'Date'
    if 'report_date' in combined_df.columns:
        combined_df['Date'] = pd.to_datetime(combined_df['report_date'])
    else:
        combined_df['Date'] = pd.Timestamp.now()

    # Create 'Department' (Handle missing values)
    if 'department' in combined_df.columns:
        combined_df['Department'] = combined_df['department'].fillna('Unknown')
    else:
        combined_df['Department'] = 'Unknown'

    # Create 'Count' (Used for volume summation)
    combined_df['Count'] = 1

    # 4. Calculate Top Level Metrics
    if 'user_email' in combined_df.columns:
        total_users = combined_df['user_email'].nunique()
    else:
        total_users = 0
        
    total_vol = len(combined_df)

    return combined_df, total_users, total_vol
