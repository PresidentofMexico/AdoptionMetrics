import sys
import os
import pandas as pd
import numpy as np

# --- PATH FIX ---
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
# ----------------

from src.config import DEPT_RATES, AVERAGE_HOURLY_RATE

class MetricsEngine:
    def __init__(self, df):
        self.df = df.copy()
        
    def calculate_roi(self, assumptions=None, discount_rate=0.0):
        if assumptions is None:
            assumptions = {
                'Standard Chat': 5, 
                'ChatGPT Messages': 5,
                'Investment Research': 15, 
                'BlueFlame Messages': 15,
                'Advanced Data Analysis': 30,
                'Tool Messages': 30,
                'Custom GPTs': 10,
                'GPT Messages': 10,
                'Project Messages': 10
            }
            
        raw_minutes = self.df['Feature'].map(assumptions).fillna(5) * self.df['Count']
        efficiency_factor = 1 - discount_rate
        self.df['Minutes_Saved'] = raw_minutes * efficiency_factor
        self.df['Hours_Saved'] = self.df['Minutes_Saved'] / 60
        
        # Department Rate Lookup
        self.df['Hourly_Rate'] = self.df['Department'].apply(
            lambda x: DEPT_RATES.get(str(x).replace('_', ' ').title(), AVERAGE_HOURLY_RATE)
        )
        
        self.df['Dollar_Value'] = self.df['Hours_Saved'] * self.df['Hourly_Rate']
        return self.df

    def get_retention_matrix(self):
        if self.df.empty: return pd.DataFrame()

        monthly_users = self.df.groupby(pd.Grouper(key='Date', freq='M'))['Email'].unique().reset_index()
        monthly_users['Date_Str'] = monthly_users['Date'].dt.strftime('%Y-%m')
        monthly_users = monthly_users.sort_values('Date')
        
        retention_data = []
        months = monthly_users['Date_Str'].tolist()
        user_sets = monthly_users['Email'].tolist()
        
        if len(months) < 2: return pd.DataFrame()

        for i in range(len(months) - 1):
            current_month = months[i]
            next_month = months[i+1]
            current_users = set(user_sets[i])
            next_users = set(user_sets[i+1])
            retained = current_users.intersection(next_users)
            
            retention_rate = (len(retained) / len(current_users)) * 100 if len(current_users) > 0 else 0
            
            retention_data.append({
                'Month': current_month,
                'Next_Month': next_month,
                'Active_Users': len(current_users),
                'Retained_Users': len(retained),
                'Retention_Rate': retention_rate
            })
            
        return pd.DataFrame(retention_data)
