"""Shared package for Fleaflicker dashboards and CLIs."""

from .api import FleaflickerAPI
from .dashboard import Dashboard
from .tui import FleaflickerDashboardApp

__all__ = ["FleaflickerAPI", "Dashboard", "FleaflickerDashboardApp", "__version__"]
__version__ = "0.1.0"
