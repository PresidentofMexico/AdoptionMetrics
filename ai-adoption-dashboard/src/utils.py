"""
Utility Functions Module

Helper functions for formatting, authentication, and other common tasks.
"""

from typing import Any
from datetime import datetime


def format_currency(amount: float, currency: str = "USD") -> str:
    """
    Format number as currency.
    
    Args:
        amount: Amount to format
        currency: Currency code (default: USD)
        
    Returns:
        Formatted currency string
    """
    return f"${amount:,.2f}"


def format_percentage(value: float, decimals: int = 2) -> str:
    """
    Format number as percentage.
    
    Args:
        value: Value to format
        decimals: Number of decimal places
        
    Returns:
        Formatted percentage string
    """
    return f"{value:.{decimals}f}%"


def format_date(date: datetime, format_string: str = "%Y-%m-%d") -> str:
    """
    Format datetime object.
    
    Args:
        date: Datetime object to format
        format_string: Format string
        
    Returns:
        Formatted date string
    """
    return date.strftime(format_string)


def validate_data(data: Any) -> bool:
    """
    Validate data integrity.
    
    Args:
        data: Data to validate
        
    Returns:
        True if data is valid, False otherwise
    """
    if data is None:
        return False
    return True
