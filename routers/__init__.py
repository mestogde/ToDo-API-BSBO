# routers/__init__.py
from . import tasks
from . import stats
from . import auth
from . import admin

__all__ = ["tasks", "stats", "auth", "admin"]