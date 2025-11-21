import pandas as pd
import glob
import os
import re
from . import config

class DataProcessor:
    def __init__(self):
        self.data_dir = config.DATA_DIR
        self.month_map = {
            'January': 1, 'February': 2, 'March': 3, 'April': 4, 'May': 5, 'June': 6,
            'July': 7, 'August': 8, 'September': 9, 'October': 10, 'November': 11, 'December': 12
        }

    def get_date_from_filename(self, filename):
        """
        Extracts date from filenames like:
        - "Openai Eldridge ... report October.csv"
        - "blueflame_usage...October2025..."
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
        
        # 2. Fallback for other patterns
        return pd.Timestamp.now()

    def load_openai_data(self):
        """Loads all OpenAI files matching the glob pattern."""
        all_files = glob.glob(os.path.join(self.data_dir, config.OPENAI_GLOB_PATTERN))
        df_list = []
        
        for filename in all_files:
            try:
                df = pd.read_csv(filename)
                # Normalize columns: lowercase and replace spaces with underscores
                df.columns = [c.lower().replace(' ', '_') for c in df.columns]
                
                # Add date derived from filename
                report_date = self.get_date_from_filename(filename)
                df['report_date'] = report_date
                df['month'] = report_date.strftime('%Y-%m')
                
                # Ensure 'user_email' exists (map 'email' -> 'user_email' if needed)
                if 'user_email' not in df.columns and 'email' in df.columns:
                    df['user_email'] = df['email']
                
                df_list.append(df)
            except Exception as e:
                print(f"Error loading OpenAI file {filename}: {e}")
                continue
                
        if not df_list:
            return pd.DataFrame()
            
        return pd.concat(df_list, ignore_index=True)

    def load_blueflame_data(self):
        """Loads all BlueFlame files matching the glob pattern."""
        all_files = glob.glob(os.path.join(self.data_dir, config.BLUEFLAME_GLOB_PATTERN))
        df_list = []
        
        for filename in all_files:
            try:
                df = pd.read_csv(filename)
                df.columns = [c.lower().replace(' ', '_') for c in df.columns]
                
                report_date = self.get_date_from_filename(filename)
                df['report_date'] = report_date
                df['month'] = report_date.strftime('%Y-%m')
                
                df_list.append(df)
            except Exception as e:
                print(f"Error loading BlueFlame file {filename}: {e}")
        
        if not df_list:
            return pd.DataFrame()
            
        return pd.concat(df_list, ignore_index=True)
