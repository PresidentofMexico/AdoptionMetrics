"""
Configuration Module

Constants for price per license, ROI assumptions, and other configuration values.
"""

# Pricing Configuration
PRICE_PER_LICENSE = 20.0  # USD per license per month

# ROI Assumptions
HOURS_SAVED_PER_WEEK_PER_USER = 5.0  # Average hours saved per user per week
AVERAGE_HOURLY_RATE = 50.0  # USD per hour
WEEKS_PER_MONTH = 4.33  # Average weeks per month

# Departmental Hourly Rates (Fully Loaded)
# Used for granular ROI modeling in metrics.py
DEPT_RATES = {
    'Legal': 250.0,
    'Finance': 175.0,
    'Engineering': 150.0,
    'Product': 140.0,
    'Sales': 120.0,
    'Marketing': 100.0,
    'Human Resources': 90.0,
    'Operations': 80.0,
    'Administrative': 60.0
}

# Adoption Thresholds
LOW_ADOPTION_THRESHOLD = 30.0  # Percentage
MEDIUM_ADOPTION_THRESHOLD = 60.0  # Percentage
HIGH_ADOPTION_THRESHOLD = 80.0  # Percentage

# Data Configuration
DATA_DIR = "data"
CHATGPT_EXPORT_FILENAME = "chatgpt_export.csv"
BF_EXPORT_FILENAME = "bf_export.csv"
HEADCOUNT_FILENAME = "headcount.csv"
