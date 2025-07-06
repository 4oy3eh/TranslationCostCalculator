# config/__init__.py
"""
Translation Cost Calculator - Configuration Package

Configuration management for database, settings, and application constants.
"""

from .settings import Settings
from .database import DatabaseManager

__all__ = ['Settings', 'DatabaseManager']