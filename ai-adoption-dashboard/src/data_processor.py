import pandas as pd
import re
import os
from pathlib import Path

class DataProcessor:
    def __init__(self, employee_file_path=None):
        self.employee_map = {}
        # Robust path handling
        if employee_file_path:
            if os.path.exists(employee_file_path):
                self._load_employee_mapping(employee_file_path)
            else:
                print(f"⚠️ Warning: Employee file not found at {employee_file_path}")

    def _load_employee_mapping(self, filepath):
        """Creates a 'Source of Truth' dictionary for Departments."""
        try:
            df = pd.read_csv(filepath)
            # Normalize columns: lowercase, strip whitespace
            df.columns = [c.strip() for c in df.columns]
            
            # Find Email and Function columns robustly
            email_col = next((c for c in df.columns if 'email' in c.lower()), 'Email')
            func_col = next((c for c in df.columns if 'function' in c.lower()), 'Function')
            
            df[email_col] = df[email_col].astype(str).str.lower().str.strip()
            df[func_col] = df[func_col].astype(str).str.strip()
            self.employee_map = dict(zip(df[email_col], df[func_col]))
        except Exception as e:
            print(f"⚠️ Warning: Could not process employee file: {e}")

    def process_blueflame(self, df: pd.DataFrame, filename: str) -> pd.DataFrame:
        """Normalizes BlueFlame 'Wide' format (Months as columns)"""
        # Identify date columns (e.g., '25-Apr')
        date_cols = [c for c in df.columns if re.match(r'\d{2}-[A-Z][a-z]{2}', c)]
        
        if not date_cols:
            return pd.DataFrame()

        # Melt (Unpivot)
        melted = df.melt(id_vars=['User ID'], value_vars=date_cols, var_name='Date_Str', value_name='Count')
        
        # Clean
        melted = melted.dropna(subset=['Count'])
        melted['Count'] = pd.to_numeric(melted['Count'], errors='coerce').fillna(0)
        melted = melted[melted['Count'] > 0]
        
        # Parse Dates
        melted['Date'] = pd.to_datetime(melted['Date_Str'], format='%y-%b', errors='coerce')
        
        # Map Metadata
        melted['Email'] = melted['User ID'].astype(str).str.lower().str.strip()
        melted['Name'] = melted['Email'].apply(lambda x: x.split('@')[0].replace('.', ' ').title())
        melted['Department'] = melted['Email'].map(self.employee_map).fillna('Unknown')
        melted['Tool'] = 'BlueFlame'
        melted['Feature'] = 'Investment Research' # Specific tag for high-value work
        
        return melted[['Date', 'Email', 'Name', 'Department', 'Tool', 'Feature', 'Count']]

    def process_openai(self, df: pd.DataFrame, filename: str) -> pd.DataFrame:
        """Normalizes OpenAI Monthly Export"""
        records = []
        feature_mapping = {
            'messages': 'Standard Chat',
            'tool_messages': 'Advanced Data Analysis', 
            'gpt_messages': 'Custom GPTs'
        }
        
        # Ensure column names are lower case for easier matching
        df.columns = [c.lower() for c in df.columns]
        
        for _, row in df.iterrows():
            email = str(row.get('email', '')).lower().strip()
            if not email or email == 'nan': continue
            
            try:
                date = pd.to_datetime(row.get('period_start'))
            except:
                continue
                
            name = row.get('name', email.split('@')[0])
            
            # Department Logic: Try Map -> Fallback to JSON parse -> 'Unknown'
            dept = self.employee_map.get(email)
            if not dept:
                raw_dept = str(row.get('department', ''))
                if '[' in raw_dept:
                    try:
                        dept = raw_dept.strip('[]"\' ').title()
                    except:
                        dept = 'Unknown'
                else:
                    dept = 'Unknown'
            
            # Create rows for each feature
            for col, feature_name in feature_mapping.items():
                count = pd.to_numeric(row.get(col, 0), errors='coerce')
                if count > 0:
                    records.append({
                        'Date': date,
                        'Email': email,
                        'Name': name,
                        'Department': dept,
                        'Tool': 'ChatGPT',
                        'Feature': feature_name,
                        'Count': count
                    })
                    
        return pd.DataFrame(records)

    def get_unified_data(self, bf_paths=None, openai_paths=None):
        """
        Main entry point. Handles lists of file paths OR file objects.
        """
        dfs = []
        
        # Helper to read CSV regardless of input type
        def read_csv_safe(file_input):
            if isinstance(file_input, str) or isinstance(file_input, Path):
                return pd.read_csv(file_input), os.path.basename(file_input)
            else: # Streamlit UploadedFile object
                file_input.seek(0)
                return pd.read_csv(file_input), file_input.name

        if bf_paths:
            for f in bf_paths:
                try:
                    df, fname = read_csv_safe(f)
                    dfs.append(self.process_blueflame(df, fname))
                except Exception as e:
                    print(f"Error processing BlueFlame file {f}: {e}")

        if openai_paths:
            for f in openai_paths:
                try:
                    df, fname = read_csv_safe(f)
                    dfs.append(self.process_openai(df, fname))
                except Exception as e:
                    print(f"Error processing OpenAI file {f}: {e}")
             
        if not dfs: return pd.DataFrame()
        return pd.concat(dfs, ignore_index=True)
