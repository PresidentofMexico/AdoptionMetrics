import pandas as pd
import numpy as np
from src.config import DEPT_RATES, AVERAGE_HOURLY_RATE

class MetricsEngine:
    def __init__(self, df):
        self.df = df.copy()
        
    def calculate_roi(self, assumptions=None, discount_rate=0.0):
        """
        Calculates time and dollar savings based on feature type and department rates.
        
        Args:
            discount_rate (float): 0.0 to 1.0. 
                                   0.2 means "Remove 20% of value to account for errors/iterations".
        """
        if assumptions is None:
            # Default minutes saved per interaction type
            assumptions = {
                'Standard Chat': 5, 
                'ChatGPT Messages': 5,
                'Investment Research': 15, # High value (BlueFlame)
                'BlueFlame Messages': 15,
                'Advanced Data Analysis': 30,
                'Tool Messages': 30,
                'Custom GPTs': 10,
                'Project Messages': 10
            }
            
        # 1. Map Gross Minutes (Optimistic)
        raw_minutes = self.df['Feature'].map(assumptions).fillna(5) * self.df['Count']
        
        # 2. Apply Discount Factor (The "Reality Check")
        efficiency_factor = 1 - discount_rate
        
        self.df['Minutes_Saved'] = raw_minutes * efficiency_factor
        self.df['Hours_Saved'] = self.df['Minutes_Saved'] / 60
        
        # 3. Apply Granular Hourly Rates [UPDATED]
        # Lookup rate based on Department, fallback to AVERAGE_HOURLY_RATE
        self.df['Hourly_Rate'] = self.df['Department'].apply(
            lambda x: DEPT_RATES.get(str(x).replace('_', ' ').title(), AVERAGE_HOURLY_RATE)
        )
        
        self.df['Dollar_Value'] = self.df['Hours_Saved'] * self.df['Hourly_Rate']
        
        return self.df

    def get_efficiency_quadrant(self):
        """
        Generates data for the "Volume vs. Diversity" scatter plot.
        """
        stats = self.df.groupby(['Department']).agg(
            Active_Users=('Email', 'nunique'),
            Total_Volume=('Count', 'sum'),
            Unique_Features=('Feature', 'nunique'),
            Tools_Used=('Tool', 'nunique')
        ).reset_index()
        
        stats['Intensity'] = stats['Total_Volume'] / stats['Active_Users']
        stats['Median_Vol'] = stats['Total_Volume'].median()
        stats['Median_Diversity'] = stats['Unique_Features'].median()
        
        return stats

    def get_user_leaderboard(self):
        """
        Generates a clean user table with 'Efficiency Badges'.
        """
        user_stats = self.df.groupby(['Name', 'Department', 'Email']).agg(
            Total_Interactions=('Count', 'sum'),
            Tools_Used=('Tool', lambda x: list(set(x))),
            Last_Active=('Date', 'max')
        ).reset_index()

        p90 = user_stats['Total_Interactions'].quantile(0.90)
        p70 = user_stats['Total_Interactions'].quantile(0.70)
        
        def get_badge(vol):
            if vol >= p90: return "🔥 Champion"
            if vol >= p70: return "⚡ Power User"
            return "🌱 Explorer"

        user_stats['Status'] = user_stats['Total_Interactions'].apply(get_badge)
        return user_stats.sort_values('Total_Interactions', ascending=False)

    def get_retention_matrix(self):
        """
        Calculates Monthly Retention: % of users from Month M who returned in Month M+1.
        """
        if self.df.empty:
            return pd.DataFrame()

        # 1. Identify active users per month
        monthly_users = self.df.groupby(pd.Grouper(key='Date', freq='M'))['Email'].unique().reset_index()
        monthly_users['Date_Str'] = monthly_users['Date'].dt.strftime('%Y-%m')
        monthly_users = monthly_users.sort_values('Date')
        
        retention_data = []
        
        # 2. Iterate to compare Month i vs Month i+1
        months = monthly_users['Date_Str'].tolist()
        user_sets = monthly_users['Email'].tolist()
        
        if len(months) < 2:
            return pd.DataFrame()

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
