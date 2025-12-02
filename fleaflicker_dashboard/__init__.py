"""Shared package for Fleaflicker dashboards and CLIs."""

from .api import ApiError, FleaflickerAPI
from .dashboard import Dashboard
from .tui import FleaflickerDashboardApp

__all__ = ["ApiError", "FleaflickerAPI", "Dashboard", "FleaflickerDashboardApp", "__version__"]
__version__ = "0.1.0"
