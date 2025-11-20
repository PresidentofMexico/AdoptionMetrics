import pandas as pd
import re
from pathlib import Path

class DataProcessor:
    def __init__(self, employee_file_path=None):
        self.employee_map = {}
        if employee_file_path:
            self._load_employee_mapping(employee_file_path)

    def _load_employee_mapping(self, filepath):
        """Creates a 'Source of Truth' dictionary for Departments."""
        try:
            df = pd.read_csv(filepath)
            # Normalize: lowercase emails, strip whitespace
            df['Email'] = df['Email'].astype(str).str.lower().str.strip()
            df['Function'] = df['Function'].astype(str).str.strip()
            self.employee_map = dict(zip(df['Email'], df['Function']))
        except Exception as e:
            print(f"⚠️ Warning: Could not load employee file: {e}")

    def process_blueflame(self, df: pd.DataFrame, filename: str) -> pd.DataFrame:
        """Normalizes BlueFlame 'Wide' format (Months as columns)"""
        # Identify date columns (e.g., '25-Apr')
        date_cols = [c for c in df.columns if re.match(r'\d{2}-[A-Z][a-z]{2}', c)]
        
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
            'tool_messages': 'Advanced Data Analysis', # High ROI
            'gpt_messages': 'Custom GPTs'
        }
        
        for _, row in df.iterrows():
            email = str(row.get('email', '')).lower().strip()
            if not email or email == 'nan': continue
            
            try:
                date = pd.to_datetime(row['period_start'])
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

    def get_unified_data(self, bf_files, openai_files):
        """Main entry point to get all data"""
        dfs = []
        for file in bf_files:
             dfs.append(self.process_blueflame(pd.read_csv(file), file.name))
        for file in openai_files:
             dfs.append(self.process_openai(pd.read_csv(file), file.name))
             
        if not dfs: return pd.DataFrame()
        return pd.concat(dfs, ignore_index=True)
