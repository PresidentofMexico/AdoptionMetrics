import pandas as pd
import re
import os
import glob
import streamlit as st
import datetime
from src.config import HEADCOUNT_FILENAME, CHATGPT_EXPORT_PATTERN, BLUEFLAME_EXPORT_PATTERN

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

            # Normalize emails
            df[email_col] = df[email_col].astype(str).str.lower().str.strip()
            df[func_col] = df[func_col].astype(str).str.strip()
            
            # --- FIX: Remove duplicates in headcount file (Keep last entry) ---
            df = df.drop_duplicates(subset=[email_col], keep='last')
            
            self.employee_map = dict(zip(df[email_col], df[func_col]))
            self.debug_log.append(f"✅ Mapped {len(self.employee_map)} employees.")
            
        except Exception as e:
            self.debug_log.append(f"❌ Error processing employee file: {str(e)}")

    def _get_empty_schema(self):
        return pd.DataFrame(columns=['Date', 'Email', 'Name', 'Department', 'Tool', 'Feature', 'Count'])

    def process_blueflame(self, df: pd.DataFrame, filename: str) -> pd.DataFrame:
        # Clean columns to remove invisible whitespace
        df.columns = [str(c).strip() for c in df.columns]

        # Identify date columns (e.g., '25-Apr' or '1-Oct')
        # Regex updated to handle 1 or 2 digits: \d{1,2}
        date_cols = [c for c in df.columns if re.match(r'^\d{1,2}-[A-Z][a-z]{2}', c)]
        
        if not date_cols:
            self.debug_log.append(f"⚠️ No date columns found in BF file: {filename}")
            return self._get_empty_schema()

        # Identify User Column (flexible matching)
        user_col = next((c for c in df.columns if 'user' in c.lower() and 'id' in c.lower()), None)
        if not user_col:
             # Fallback: try finding 'Email'
             user_col = next((c for c in df.columns if 'email' in c.lower()), None)
        
        if not user_col:
            return self._get_empty_schema()

        melted = df.melt(id_vars=[user_col], value_vars=date_cols, var_name='Date_Str', value_name='Count')
        melted = melted.dropna(subset=['Count'])
        melted['Count'] = pd.to_numeric(melted['Count'], errors='coerce').fillna(0)
        melted = melted[melted['Count'] > 0]
        
        # --- FIX: Date Parsing Logic ---
        # 1. Try to find year in filename (e.g., "October2025")
        year_match = re.search(r'20\d{2}', filename)
        year = year_match.group(0) if year_match else str(datetime.datetime.now().year)
        
        # 2. Append year and parse
        melted['Date'] = pd.to_datetime(melted['Date_Str'].astype(str).str.strip() + f"-{year}", format='%d-%b-%Y', errors='coerce')
        
        melted['Email'] = melted[user_col].astype(str).str.lower().str.strip()
        
        # --- FIX: STRICT FILTERS for "Total" rows ---
        # 1. Drop rows where Email is just "nan" or empty
        melted = melted[melted['Email'] != 'nan']
        melted = melted[melted['Email'] != '']
        
        # 2. Drop rows that contain "total", "sum" in the ID
        blacklist = ['total', 'sum', 'average', 'count']
        melted = melted[~melted['Email'].str.contains('|'.join(blacklist), case=False, na=False)]
        
        # 3. Require a valid email structure (contains @ and .)
        melted = melted[melted['Email'].str.match(r'^[^@]+@[^@]+\.[^@]+')]

        melted['Department'] = melted['Email'].map(self.employee_map).fillna('Unassigned')
        melted['Name'] = melted['Email'].apply(lambda x: x.split('@')[0].replace('.', ' ').title())
        
        melted['Tool'] = 'BlueFlame'
        melted['Feature'] = 'BlueFlame Messages' 
        
        # --- FIX: Aggregate daily counts ---
        # Sums up if duplicates exist in the source file
        melted = melted.groupby(['Date', 'Email', 'Name', 'Department', 'Tool', 'Feature'], as_index=False)['Count'].sum()
        
        return melted[['Date', 'Email', 'Name', 'Department', 'Tool', 'Feature', 'Count']]

    def process_openai(self, df: pd.DataFrame, filename: str) -> pd.DataFrame:
        records = []
        
        df.columns = [c.lower().strip() for c in df.columns]
        
        for _, row in df.iterrows():
            email = str(row.get('email', '')).lower().strip()
            
            # --- FIX: Strict Email Validation ---
            if not email or '@' not in email: continue
            if 'total' in email.lower(): continue

            try:
                date = pd.to_datetime(row.get('period_start'))
            except:
                continue
                
            name = email.split('@')[0].replace('.', ' ').title()
            dept = self.employee_map.get(email, 'Unassigned')
            
            # --- FIX: Avoid Double Counting ---
            # Use 'messages' as Total.
            total_msgs = pd.to_numeric(row.get('messages', 0), errors='coerce')
            tool_msgs = pd.to_numeric(row.get('tool_messages', 0), errors='coerce')
            gpt_msgs = pd.to_numeric(row.get('gpt_messages', 0), errors='coerce')
            project_msgs = pd.to_numeric(row.get('project_messages', 0), errors='coerce')
            
            # Sub-features
            sub_features = {
                'Tool Messages': tool_msgs,
                'GPT Messages': gpt_msgs,
                'Project Messages': project_msgs
            }
            
            # Calculate Standard Chat (The Remainder)
            sub_total = tool_msgs + gpt_msgs + project_msgs
            
            # LOGIC CHECK: Is 'messages' inclusive or exclusive?
            # Standard Assumption: messages is Total.
            # Safety Check: If Total < Sub-parts, then 'messages' must be exclusive (Standard Chat only).
            
            if total_msgs < sub_total:
                # Case: 'messages' column represents ONLY Standard Chat
                standard_chat_count = total_msgs
            else:
                # Case: 'messages' column represents Total (Subtract parts to get Standard Chat)
                standard_chat_count = total_msgs - sub_total
            
            # Safety clamp
            if standard_chat_count < 0: 
                standard_chat_count = 0
            
            if standard_chat_count > 0:
                records.append({
                    'Date': date, 'Email': email, 'Name': name, 'Department': dept,
                    'Tool': 'ChatGPT', 'Feature': 'Standard Chat', 'Count': standard_chat_count
                })
                
            for feature_name, count in sub_features.items():
                if count > 0:
                    records.append({
                        'Date': date, 'Email': email, 'Name': name, 'Department': dept,
                        'Tool': 'ChatGPT', 'Feature': feature_name, 'Count': count
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
        
        # --- FIX: STRICT DEDUPLICATION ---
        # Keeps only the first occurrence of valid data points
        initial_count = len(result)
        result = result.drop_duplicates(subset=['Date', 'Email', 'Tool', 'Feature'])
        final_count = len(result)
        
        if initial_count != final_count:
            self.debug_log.append(f"⚠️ Removed {initial_count - final_count} duplicate records.")
        
        if 'Feature' not in result.columns:
             result['Feature'] = 'Unknown'
             
        return result

# --- Unified Data Loader ---
@st.cache_data(show_spinner="Processing Data...")
def load_data():
    """
    Centralized data loading function. Scans directories and processes files.
    """
    # Robust path finding
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    # Search current dir, parent, and data subfolders
    search_paths = [script_dir, repo_root, os.path.join(script_dir, "../data"), os.path.join(repo_root, "data")]
    
    emp_path = None
    bf_files = []
    openai_files = []

    for folder in search_paths:
        if not os.path.exists(folder): continue
        
        # Find Headcount File
        if not emp_path:
            found = glob.glob(os.path.join(folder, f"{HEADCOUNT_FILENAME}*"))
            if found: emp_path = found[0]
    
        # Find Usage Files - Aggressive Fallback
        # 1. Try Config Patterns
        for pattern in BLUEFLAME_EXPORT_PATTERN:
            bf_files.extend(glob.glob(os.path.join(folder, pattern)))
        for pattern in CHATGPT_EXPORT_PATTERN:
            openai_files.extend(glob.glob(os.path.join(folder, pattern)))
            
        # 2. Fallback: Search for any file with "blueflame" or "openai" in name if lists are empty
        if not bf_files:
             bf_files.extend(glob.glob(os.path.join(folder, "*blueflame*.csv")))
             bf_files.extend(glob.glob(os.path.join(folder, "*BlueFlame*.csv")))
             
        if not openai_files:
             openai_files.extend(glob.glob(os.path.join(folder, "*openai*.csv")))
             openai_files.extend(glob.glob(os.path.join(folder, "*OpenAI*.csv")))
    
    # Deduplicate file lists
    bf_files = list(set(bf_files))
    openai_files = list(set(openai_files))

    processor = DataProcessor(emp_path)
    # Remove duplicates
    df = processor.get_unified_data(bf_paths=bf_files, openai_paths=openai_files)
    
    # Add File Detection Log
    processor.debug_log.append(f"📂 Found {len(bf_files)} BlueFlame files")
    processor.debug_log.append(f"📂 Found {len(openai_files)} OpenAI files")
    
    return df, emp_path, processor.debug_log
