"""
Charts Module

Plotly chart definitions for visualizing adoption metrics and trends.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Optional, List


def create_adoption_trend_chart(df: pd.DataFrame, 
                                date_column: str = "date",
                                value_column: str = "adoption_rate") -> go.Figure:
    """
    Create a line chart showing adoption trends over time.
    
    Args:
        df: DataFrame with time series data
        date_column: Column name for dates
        value_column: Column name for values
        
    Returns:
        Plotly figure object
    """
    fig = px.line(
        df,
        x=date_column,
        y=value_column,
        title="Adoption Trend Over Time",
        labels={value_column: "Adoption Rate (%)", date_column: "Date"}
    )
    
    fig.update_layout(
        hovermode="x unified",
        showlegend=True
    )
    
    return fig


def create_department_bar_chart(df: pd.DataFrame,
                                department_column: str = "department",
                                value_column: str = "user_count") -> go.Figure:
    """
    Create a bar chart showing metrics by department.
    
    Args:
        df: DataFrame with department data
        department_column: Column name for departments
        value_column: Column name for values
        
    Returns:
        Plotly figure object
    """
    fig = px.bar(
        df,
        x=department_column,
        y=value_column,
        title="Users by Department",
        labels={value_column: "Number of Users", department_column: "Department"}
    )
    
    fig.update_layout(
        xaxis_tickangle=-45,
        showlegend=False
    )
    
    return fig


def create_roi_chart(df: pd.DataFrame,
                    date_column: str = "date",
                    roi_column: str = "roi") -> go.Figure:
    """
    Create a chart showing ROI over time.
    
    Args:
        df: DataFrame with ROI data
        date_column: Column name for dates
        roi_column: Column name for ROI values
        
    Returns:
        Plotly figure object
    """
    fig = px.area(
        df,
        x=date_column,
        y=roi_column,
        title="ROI Trend",
        labels={roi_column: "ROI (%)", date_column: "Date"}
    )
    
    fig.update_traces(
        fill='tozeroy',
        line_color='green'
    )
    
    return fig


def create_user_engagement_heatmap(df: pd.DataFrame,
                                   x_column: str = "week",
                                   y_column: str = "user",
                                   value_column: str = "sessions") -> go.Figure:
    """
    Create a heatmap showing user engagement patterns.
    
    Args:
        df: DataFrame with engagement data
        x_column: Column for x-axis (e.g., time periods)
        y_column: Column for y-axis (e.g., users)
        value_column: Column for heatmap values
        
    Returns:
        Plotly figure object
    """
    pivot_df = df.pivot(index=y_column, columns=x_column, values=value_column)
    
    fig = go.Figure(data=go.Heatmap(
        z=pivot_df.values,
        x=pivot_df.columns,
        y=pivot_df.index,
        colorscale='Viridis'
    ))
    
    fig.update_layout(
        title="User Engagement Heatmap",
        xaxis_title=x_column.capitalize(),
        yaxis_title=y_column.capitalize()
    )
    
    return fig


def create_leaderboard_chart(df: pd.DataFrame,
                             user_column: str = "user",
                             metric_column: str = "sessions",
                             top_n: int = 10) -> go.Figure:
    """
    Create a horizontal bar chart for leaderboard display.
    
    Args:
        df: DataFrame with user metrics
        user_column: Column name for users
        metric_column: Column name for metric to rank by
        top_n: Number of top users to show
        
    Returns:
        Plotly figure object
    """
    # Sort and get top N
    top_users = df.nlargest(top_n, metric_column)
    
    fig = px.bar(
        top_users,
        x=metric_column,
        y=user_column,
        orientation='h',
        title=f"Top {top_n} Users by {metric_column.replace('_', ' ').title()}",
        labels={metric_column: metric_column.replace('_', ' ').title(), 
                user_column: "User"}
    )
    
    fig.update_layout(
        yaxis={'categoryorder': 'total ascending'},
        showlegend=False
    )
    
    return fig
