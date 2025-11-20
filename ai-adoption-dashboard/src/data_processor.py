import pandas as pd
import re
import os
import streamlit as st

class DataProcessor:
    def __init__(self, employee_file_path=None):
        self.employee_map = {}
        self.debug_log = []
        
        if employee_file_path:
            if os.path.exists(employee_file_path):
                self._load_employee_mapping(employee_file_path)
            else:
                self.debug_log.append(f"❌ Employee file not found at path: {employee_file_path}")
        else:
            self.debug_log.append("⚠️ No employee file path provided")

    def _load_employee_mapping(self, filepath):
        """Creates a 'Source of Truth' dictionary for Departments."""
        try:
            # Use utf-8-sig to handle BOM characters often found in Excel CSV exports
            try:
                df = pd.read_csv(filepath, encoding='utf-8-sig')
            except:
                df = pd.read_csv(filepath, encoding='latin1')

            # Normalize columns: lowercase, strip whitespace
            df.columns = [c.strip() for c in df.columns]
            
            # Find Email column (robust search)
            email_col = next((c for c in df.columns if 'email' in c.lower()), None)
            
            # Find Department column (Look for Function first, then Dept)
            func_col = next((c for c in df.columns if 'function' in c.lower()), None)
            if not func_col:
                 func_col = next((c for c in df.columns if 'department' in c.lower()), None)

            if not email_col or not func_col:
                self.debug_log.append(f"❌ Column Missing in Emp File. Found: {df.columns.tolist()}")
                return

            # Clean data for matching
            df[email_col] = df[email_col].astype(str).str.lower().str.strip()
            df[func_col] = df[func_col].astype(str).str.strip()
            
            # Create the master dictionary {email: department}
            self.employee_map = dict(zip(df[email_col], df[func_col]))
            
            # DEBUG: Log success
            self.debug_log.append(f"✅ Mapped {len(self.employee_map)} employees.")
            # Show first 3 matches for sanity check
            sample_keys = list(self.employee_map.keys())[:3]
            self.debug_log.append(f"Sample Emails in Roster: {sample_keys}")
            
        except Exception as e:
            self.debug_log.append(f"❌ Error processing employee file: {str(e)}")

    def _get_empty_schema(self):
        """Returns an empty DataFrame with the correct columns to prevent KeyErrors."""
        return pd.DataFrame(columns=['Date', 'Email', 'Name', 'Department', 'Tool', 'Feature', 'Count'])

    def process_blueflame(self, df: pd.DataFrame, filename: str) -> pd.DataFrame:
        # Identify date columns (e.g., '25-Apr')
        date_cols = [c for c in df.columns if re.match(r'\d{2}-[A-Z][a-z]{2}', c)]
        
        if not date_cols:
            return self._get_empty_schema()

        melted = df.melt(id_vars=['User ID'], value_vars=date_cols, var_name='Date_Str', value_name='Count')
        melted = melted.dropna(subset=['Count'])
        melted['Count'] = pd.to_numeric(melted['Count'], errors='coerce').fillna(0)
        melted = melted[melted['Count'] > 0]
        melted['Date'] = pd.to_datetime(melted['Date_Str'], format='%y-%b', errors='coerce')
        
        # Map Metadata
        melted['Email'] = melted['User ID'].astype(str).str.lower().str.strip()
        
        # STRICT MAPPING: Use Map, fallback to 'Unassigned' (Do not use CSV data)
        melted['Department'] = melted['Email'].map(self.employee_map).fillna('Unassigned')
        
        melted['Name'] = melted['Email'].apply(lambda x: x.split('@')[0].replace('.', ' ').title())
        melted['Tool'] = 'BlueFlame'
        melted['Feature'] = 'Investment Research' 
        
        return melted[['Date', 'Email', 'Name', 'Department', 'Tool', 'Feature', 'Count']]

    def process_openai(self, df: pd.DataFrame, filename: str) -> pd.DataFrame:
        records = []
        feature_mapping = {
            'messages': 'Standard Chat',
            'tool_messages': 'Advanced Data Analysis', 
            'gpt_messages': 'Custom GPTs'
        }
        
        df.columns = [c.lower() for c in df.columns]
        
        for _, row in df.iterrows():
            email = str(row.get('email', '')).lower().strip()
            if not email or email == 'nan': continue
            
            try:
                # Handle different date formats
                date = pd.to_datetime(row.get('period_start'))
            except:
                continue
                
            name = row.get('name', email.split('@')[0])
            
            # STRICT MAPPING
            dept = self.employee_map.get(email, 'Unassigned')
            
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
        
        if not records:
            return self._get_empty_schema()
            
        return pd.DataFrame(records)

    def get_unified_data(self, bf_paths=None, openai_paths=None):
        dfs = []
        
        def read_csv_safe(path):
            try:
                return pd.read_csv(path, encoding='utf-8-sig'), os.path.basename(path)
            except:
                return pd.read_csv(path, encoding='latin1'), os.path.basename(path)

        if bf_paths:
            for f in bf_paths:
                try:
                    df, fname = read_csv_safe(f)
                    dfs.append(self.process_blueflame(df, fname))
                except Exception as e:
                    self.debug_log.append(f"Error processing BF {os.path.basename(f)}: {e}")

        if openai_paths:
            for f in openai_paths:
                try:
                    df, fname = read_csv_safe(f)
                    dfs.append(self.process_openai(df, fname))
                except Exception as e:
                    self.debug_log.append(f"Error processing OpenAI {os.path.basename(f)}: {e}")
             
        if not dfs: 
            return self._get_empty_schema()
            
        result = pd.concat(dfs, ignore_index=True)
        
        # Final Safety Check: Ensure columns exist even after concat
        required_cols = ['Name', 'Department', 'Date', 'Tool', 'Count']
        for col in required_cols:
            if col not in result.columns:
                result[col] = None
                
        return result
