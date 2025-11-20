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
        try:
            try:
                df = pd.read_csv(filepath, encoding='utf-8-sig')
            except:
                df = pd.read_csv(filepath, encoding='latin1')

            df.columns = [c.strip() for c in df.columns]
            
            email_col = next((c for c in df.columns if 'email' in c.lower()), None)
            func_col = next((c for c in df.columns if 'function' in c.lower()), None)
            if not func_col:
                 func_col = next((c for c in df.columns if 'department' in c.lower()), None)

            if not email_col or not func_col:
                self.debug_log.append(f"❌ Column Missing in Emp File. Found: {df.columns.tolist()}")
                return

            df[email_col] = df[email_col].astype(str).str.lower().str.strip()
            df[func_col] = df[func_col].astype(str).str.strip()
            
            self.employee_map = dict(zip(df[email_col], df[func_col]))
            self.debug_log.append(f"✅ Mapped {len(self.employee_map)} employees.")
            
        except Exception as e:
            self.debug_log.append(f"❌ Error processing employee file: {str(e)}")

    def _get_empty_schema(self):
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
        
        melted['Email'] = melted['User ID'].astype(str).str.lower().str.strip()
        melted['Department'] = melted['Email'].map(self.employee_map).fillna('Unassigned')
        melted['Name'] = melted['Email'].apply(lambda x: x.split('@')[0].replace('.', ' ').title())
        
        melted['Tool'] = 'BlueFlame'
        # --- UPDATED LABEL ---
        melted['Feature'] = 'BlueFlame Messages' 
        
        return melted[['Date', 'Email', 'Name', 'Department', 'Tool', 'Feature', 'Count']]

    def process_openai(self, df: pd.DataFrame, filename: str) -> pd.DataFrame:
        records = []
        
        # --- UPDATED MAPPING (Original Names) ---
        feature_mapping = {
            'messages': 'ChatGPT Messages',      # Main usage
            'tool_messages': 'Tool Messages',    # Original csv header name
            'gpt_messages': 'GPT Messages',      # Original csv header name
            'project_messages': 'Project Messages' # Original csv header name
        }
        
        df.columns = [c.lower() for c in df.columns]
        
        for _, row in df.iterrows():
            email = str(row.get('email', '')).lower().strip()
            if not email or email == 'nan': continue
            
            try:
                date = pd.to_datetime(row.get('period_start'))
            except:
                continue
                
            name = row.get('name', email.split('@')[0])
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
        
        if 'Feature' not in result.columns:
             result['Feature'] = 'Unknown'
             
        return result
