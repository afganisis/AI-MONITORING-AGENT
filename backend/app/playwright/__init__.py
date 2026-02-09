"""
Playwright browser automation module for Fortex UI interaction.
"""

from .browser_manager import BrowserManager
from .actions import PlaywrightActions

__all__ = ["BrowserManager", "PlaywrightActions"]
