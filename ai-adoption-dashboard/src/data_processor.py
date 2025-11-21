import pandas as pd
import glob
import os
import streamlit as st
import sys

# --- PATH FIX ---
# Ensure we can find sibling modules if needed
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
# ----------------

from src.config import DATA_DIR, HEADCOUNT_FILENAME

class DataProcessor:
    def __init__(self, data_dir=DATA_DIR):
        self.data_dir = data_dir
        self.employee_map = {}
        self.debug_log = []
        
        # Attempt to load employee headcount for mapping
        headcount_path = os.path.join(data_dir, HEADCOUNT_FILENAME)
        # Fallback: look for any file with 'Headcount' in name if default missing
        if not os.path.exists(headcount_path):
             candidates = glob.glob(os.path.join(data_dir, "*Headcount*.csv"))
             if candidates: headcount_path = candidates[0]

        self._load_employee_mapping(headcount_path)

    def _load_employee_mapping(self, filepath):
        if os.path.exists(filepath):
            try:
                df = pd.read_csv(filepath)
                # Normalize columns
                df.columns = [c.lower() for c in df.columns]
                
                # Find Email and Department columns
                email_col = next((c for c in df.columns if 'email' in c), None)
                dept_col = next((c for c in df.columns if 'function' in c or 'department' in c), None)
                
                if email_col and dept_col:
                    df[email_col] = df[email_col].astype(str).str.lower().str.strip()
                    self.employee_map = dict(zip(df[email_col], df[dept_col]))
                else:
                    self.debug_log.append(f"⚠️ Columns missing in Headcount. Found: {df.columns}")
            except Exception as e:
                self.debug_log.append(f"❌ Error loading headcount: {e}")

    def process_blueflame(self, file_pattern="blueflame*.csv"):
        """
        Reads BlueFlame files which usually have dates as columns (pivoted).
        """
        files = glob.glob(os.path.join(self.data_dir, file_pattern))
        all_data = []

        for f in files:
            try:
                df = pd.read_csv(f)
                # Identify date columns (usually like '25-Apr')
                # We assume non-date columns are 'User ID', 'User Name', etc.
                id_vars = [c for c in df.columns if not any(char.isdigit() for char in c) or 'User' in c or 'ID' in c]
                date_vars = [c for c in df.columns if c not in id_vars]

                if not date_vars: continue

                # Unpivot
                melted = df.melt(id_vars=id_vars, value_vars=date_vars, var_name='Date_Str', value_name='Count')
                
                # Clean
                melted['Count'] = pd.to_numeric(melted['Count'], errors='coerce').fillna(0)
                melted = melted[melted['Count'] > 0]
                
                # Parse Date
                melted['Date'] = pd.to_datetime(melted['Date_Str'], format='%d-%b', errors='coerce')
                # Fallback for year assignment (assume current year or logic)
                melted['Date'] = melted['Date'].apply(lambda x: x.replace(year=2025) if pd.notnull(x) else x)

                # Map User
                user_col = next((c for c in id_vars if 'User ID' in c or 'Email' in c), id_vars[0])
                melted['Email'] = melted[user_col].astype(str).str.lower().str.strip()
                melted['Department'] = melted['Email'].map(self.employee_map).fillna('Unassigned')
                melted['Name'] = melted['Email'].apply(lambda x: x.split('@')[0].replace('.', ' ').title())
                melted['Tool'] = 'BlueFlame'
                melted['Feature'] = 'BlueFlame Messages'

                all_data.append(melted[['Date', 'Email', 'Name', 'Department', 'Tool', 'Feature', 'Count']])
            except Exception as e:
                self.debug_log.append(f"Error processing BF file {f}: {e}")

        return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()

    def process_openai(self, file_pattern="Openai*.csv"):
        """
        Reads OpenAI export files.
        """
        files = glob.glob(os.path.join(self.data_dir, file_pattern))
        all_data = []

        for f in files:
            try:
                df = pd.read_csv(f)
                # Standardize headers
                df.columns = [c.lower().replace(' ', '_') for c in df.columns]
                
                if 'period_start' not in df.columns: continue

                df['Date'] = pd.to_datetime(df['period_start'])
                df['Email'] = df['email'].astype(str).str.lower().str.strip()
                df['Name'] = df['name'].fillna(df['Email'].apply(lambda x: x.split('@')[0]))
                df['Department'] = df['Email'].map(self.employee_map).fillna('Unassigned')
                df['Tool'] = 'ChatGPT'

                # Unpivot Metrics
                metrics = {
                    'messages': 'ChatGPT Messages',
                    'tool_messages': 'Tool Messages',
                    'gpt_messages': 'GPT Messages', # Custom GPTs
                    'project_messages': 'Project Messages'
                }

                for col, feature_name in metrics.items():
                    if col in df.columns:
                        temp = df[df[col] > 0].copy()
                        temp['Feature'] = feature_name
                        temp['Count'] = temp[col]
                        all_data.append(temp[['Date', 'Email', 'Name', 'Department', 'Tool', 'Feature', 'Count']])

            except Exception as e:
                self.debug_log.append(f"Error processing OpenAI file {f}: {e}")

        return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()

    def get_unified_data(self):
        df_bf = self.process_blueflame()
        df_openai = self.process_openai()
        
        unified = pd.concat([df_bf, df_openai], ignore_index=True)
        
        if unified.empty:
            return pd.DataFrame(columns=['Date', 'Email', 'Name', 'Department', 'Tool', 'Feature', 'Count'])
            
        return unified

# --- GLOBAL LOADER FUNCTION ---
@st.cache_data(ttl=3600)
def load_and_process_data():
    processor = DataProcessor()
    df = processor.get_unified_data()
    
    if df.empty:
        return df, 0, 0
        
    total_users = df['Email'].nunique()
    total_vol = df['Count'].sum()
    
    return df, total_users, total_vol
