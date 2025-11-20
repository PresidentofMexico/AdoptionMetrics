import pandas as pd
import re
import os
from pathlib import Path

class DataProcessor:
    def __init__(self, employee_file_path=None):
        self.employee_map = {}
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
            
            # Find Email column (robust search)
            email_col = next((c for c in df.columns if 'email' in c.lower()), 'Email')
            
            # Find Department column (Robust search for 'Function' or 'Department')
            # Note: Your specific file uses 'Function' for department
            func_col = next((c for c in df.columns if 'function' in c.lower()), None)
            if not func_col:
                 func_col = next((c for c in df.columns if 'department' in c.lower()), 'Function')

            # Clean data for matching
            df[email_col] = df[email_col].astype(str).str.lower().str.strip()
            df[func_col] = df[func_col].astype(str).str.strip()
            
            # Create the master dictionary {email: department}
            self.employee_map = dict(zip(df[email_col], df[func_col]))
            print(f"✅ Loaded {len(self.employee_map)} employee records for mapping.")
            
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
        
        # --- STRICT MAPPING ---
        # Use Employee Map ONLY. If missing, label 'Unassigned'. 
        melted['Department'] = melted['Email'].map(self.employee_map).fillna('Unassigned')
        
        melted['Name'] = melted['Email'].apply(lambda x: x.split('@')[0].replace('.', ' ').title())
        melted['Tool'] = 'BlueFlame'
        melted['Feature'] = 'Investment Research' 
        
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
            
            # --- STRICT MAPPING ---
            # We IGNORE the 'department' column from the CSV completely.
            # Only the Employee Headcount file is trusted.
            dept = self.employee_map.get(email, 'Unassigned')
            
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
        """Main entry point."""
        dfs = []
        
        def read_csv_path(path):
             return pd.read_csv(path), os.path.basename(path)

        if bf_paths:
            for f in bf_paths:
                try:
                    df, fname = read_csv_path(f)
                    dfs.append(self.process_blueflame(df, fname))
                except Exception as e:
                    print(f"Error processing BlueFlame file {f}: {e}")

        if openai_paths:
            for f in openai_paths:
                try:
                    df, fname = read_csv_path(f)
                    dfs.append(self.process_openai(df, fname))
                except Exception as e:
                    print(f"Error processing OpenAI file {f}: {e}")
             
        if not dfs: return pd.DataFrame()
        return pd.concat(dfs, ignore_index=True)
