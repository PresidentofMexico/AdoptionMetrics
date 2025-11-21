import pandas as pd
import numpy as np

class MetricsEngine:
    def __init__(self, df):
        self.df = df.copy()
        
    def calculate_roi(self, hourly_rate=100, assumptions=None, discount_rate=0.0):
        """
        Calculates time and dollar savings based on feature type.
        
        Args:
            discount_rate (float): 0.0 to 1.0. 
                                   0.2 means "Remove 20% of value to account for errors/iterations".
        """
        if assumptions is None:
            # Default minutes saved per interaction type
            assumptions = {
                'Standard Chat': 5, 
                'ChatGPT Messages': 5,
                'Investment Research': 15,
                'BlueFlame Messages': 15,
                'Advanced Data Analysis': 30,
                'Tool Messages': 30,
                'GPT Messages': 10, # Aligned with DataProcessor output
                'Custom GPTs': 10,
                'Project Messages': 10
            }
            
        # 1. Map Gross Minutes (Optimistic)
        raw_minutes = self.df['Feature'].map(assumptions).fillna(5) * self.df['Count']
        
        # 2. Apply Discount Factor (The "Reality Check")
        # If discount is 80% (0.8), we keep 20% (0.2) of the value.
        efficiency_factor = 1 - discount_rate
        
        self.df['Minutes_Saved'] = raw_minutes * efficiency_factor
        self.df['Hours_Saved'] = self.df['Minutes_Saved'] / 60
        self.df['Dollar_Value'] = self.df['Hours_Saved'] * hourly_rate
        
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
