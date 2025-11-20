"""
Employee Matcher Module

Logic to link users to departments via headcount file.
Matches usage data with employee organizational data.
"""

import os
from typing import Optional, Dict, List
import pandas as pd
from src.config import DATA_DIR, HEADCOUNT_FILENAME


def load_headcount_data(data_dir: str = DATA_DIR) -> Optional[pd.DataFrame]:
    """
    Load headcount/employee data.
    
    Args:
        data_dir: Directory containing data files
        
    Returns:
        DataFrame with employee data or None if file doesn't exist
    """
    file_path = os.path.join(data_dir, HEADCOUNT_FILENAME)
    
    if not os.path.exists(file_path):
        return None
    
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        print(f"Error loading headcount data from {file_path}: {e}")
        return None


def match_users_to_departments(usage_df: pd.DataFrame, 
                               headcount_df: pd.DataFrame,
                               user_column: str = "email") -> pd.DataFrame:
    """
    Match users from usage data to their departments using headcount data.
    
    Args:
        usage_df: DataFrame with user usage data
        headcount_df: DataFrame with employee/department data
        user_column: Column name to match users on (default: "email")
        
    Returns:
        DataFrame with usage data enriched with department information
    """
    if usage_df is None or usage_df.empty:
        return pd.DataFrame()
    
    if headcount_df is None or headcount_df.empty:
        return usage_df
    
    # Perform left join to add department information
    # Adjust column names based on actual data structure
    matched_df = usage_df.merge(
        headcount_df,
        left_on=user_column,
        right_on=user_column,
        how="left"
    )
    
    return matched_df


def get_department_stats(matched_df: pd.DataFrame) -> Dict[str, any]:
    """
    Calculate statistics by department.
    
    Args:
        matched_df: DataFrame with matched user and department data
        
    Returns:
        Dictionary with department-level statistics
    """
    if matched_df is None or matched_df.empty:
        return {}
    
    stats = {
        "total_departments": 0,
        "users_by_department": {},
        "adoption_by_department": {}
    }
    
    # Add calculation logic based on actual data structure
    # This would include grouping by department and calculating metrics
    
    return stats


def get_unmatched_users(matched_df: pd.DataFrame, 
                        department_column: str = "department") -> List[str]:
    """
    Identify users that couldn't be matched to a department.
    
    Args:
        matched_df: DataFrame with matched data
        department_column: Column name for department
        
    Returns:
        List of user identifiers that couldn't be matched
    """
    if matched_df is None or matched_df.empty:
        return []
    
    # Find rows where department is null/empty
    unmatched = matched_df[matched_df[department_column].isna()]
    
    # Return list of user identifiers
    if "email" in matched_df.columns:
        return unmatched["email"].tolist()
    
    return []
