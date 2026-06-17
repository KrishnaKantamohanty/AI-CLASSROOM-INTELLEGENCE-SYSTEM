"""Helper utilities for formatting, calculations, and common operations."""
from datetime import datetime, timedelta


def format_percentage(value):
    """Format a float as a percentage string."""
    return f'{value:.1f}%'


def get_date_range(period='daily'):
    """Return (start_date, end_date) for a given period."""
    today = datetime.utcnow().date()
    if period == 'daily':
        return today, today
    elif period == 'weekly':
        start = today - timedelta(days=today.weekday())
        return start, today
    elif period == 'monthly':
        start = today.replace(day=1)
        return start, today
    elif period == 'semester':
        # Approximate: last 6 months
        start = today - timedelta(days=180)
        return start, today
    return today, today


def get_growth_indicator(current, previous):
    """Return growth percentage and direction."""
    if previous == 0:
        return 0, 'neutral'
    growth = ((current - previous) / previous) * 100
    if growth > 0:
        return round(growth, 1), 'up'
    elif growth < 0:
        return round(abs(growth), 1), 'down'
    return 0, 'neutral'


def risk_color(risk_status):
    """Return CSS color class for risk status."""
    return {
        'normal': 'success',
        'at_risk': 'warning',
        'critical': 'danger'
    }.get(risk_status, 'secondary')


def severity_color(severity):
    """Return CSS color class for alert severity."""
    return {
        'info': 'info',
        'success': 'success',
        'warning': 'warning',
        'critical': 'danger'
    }.get(severity, 'secondary')
