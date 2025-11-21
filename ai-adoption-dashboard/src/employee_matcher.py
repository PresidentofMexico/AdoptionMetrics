import pandas as pd
from . import config

class EmployeeMatcher:
    def __init__(self):
        self.headcount_df = self._load_headcount()
    
    def _load_headcount(self):
        """Loads and normalizes the headcount CSV."""
        try:
            if not config.HEADCOUNT_PATH:
                return pd.DataFrame()
                
            df = pd.read_csv(config.HEADCOUNT_PATH)
            
            # Normalize columns to lowercase/stripped for easier matching
            df.columns = [c.lower().strip() for c in df.columns]
            
            # Map common variations to standard 'email' and 'department' keys
            column_map = {
                'work email': 'email',
                'user email': 'email',
                'e-mail': 'email',
                'dept': 'department',
                'business unit': 'department',
                'function': 'department'
            }
            df = df.rename(columns=column_map)
            
            # Safety check: if 'email' still missing, try to find a column containing '@'
            if 'email' not in df.columns:
                for col in df.columns:
                    # Check first non-null value
                    first_val = df[col].dropna().astype(str).iloc[0] if not df[col].dropna().empty else ""
                    if '@' in first_val:
                        df = df.rename(columns={col: 'email'})
                        break
            
            # Standardize email format for joining
            if 'email' in df.columns:
                df['email'] = df['email'].astype(str).str.lower().str.strip()
                
            return df
        except Exception as e:
            print(f"Error loading headcount: {e}")
            return pd.DataFrame()

    def match_employees(self, usage_df, email_col='user_email'):
        """
        Merges usage data with headcount data on email.
        """
        if usage_df.empty or self.headcount_df.empty:
            return usage_df
            
        # Ensure usage email column is standardized
        if email_col in usage_df.columns:
            usage_df['match_email'] = usage_df[email_col].astype(str).str.lower().str.strip()
        else:
            # Fallback if column name differs
            return usage_df
        
        # Left join to keep all usage records, adding department info where available
        merged = pd.merge(
            usage_df, 
            self.headcount_df, 
            left_on='match_email', 
            right_on='email', 
            how='left',
            suffixes=('', '_hc')
        )
        
        # Cleanup temporary matching column
        if 'match_email' in merged.columns:
            merged = merged.drop(columns=['match_email'])
            
        return merged
