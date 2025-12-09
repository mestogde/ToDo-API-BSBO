# routers/__init__.py
from . import tasks
from . import stats
from . import auth

__all__ = ["tasks", "stats", "auth"]