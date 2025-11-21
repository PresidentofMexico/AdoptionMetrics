import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = os.path.join(BASE_DIR, "data")

# --- FILE CONFIGURATION ---
# Updated to match your uploaded headcount file
HEADCOUNT_FILE = "Employee Headcount 2025_Emails.csv"
HEADCOUNT_PATH = os.path.join(DATA_DIR, HEADCOUNT_FILE)

# Data Patterns (Glob patterns to find your monthly reports)
# Matches: "Openai Eldridge Capital Management monthly user report October.csv"
OPENAI_GLOB_PATTERN = "*monthly user report*.csv" 

# Matches: "blueflame_usage_combined_October2025_normalized.csv"
BLUEFLAME_GLOB_PATTERN = "blueflame_usage_combined_*.csv"

# --- CONSTANTS ---
# Pricing Configuration
PRICE_PER_LICENSE = 20.0  # USD per license per month

# ROI Assumptions
HOURS_SAVED_PER_WEEK_PER_USER = 5.0  # Average hours saved per user per week
AVERAGE_HOURLY_RATE = 50.0  # USD per hour
WEEKS_PER_MONTH = 4.33  # Average weeks per month

# Adoption Thresholds
LOW_ADOPTION_THRESHOLD = 30.0  # Percentage
MEDIUM_ADOPTION_THRESHOLD = 60.0  # Percentage
HIGH_ADOPTION_THRESHOLD = 80.0  # Percentage

# Cache Settings
CACHE_TTL = 3600
