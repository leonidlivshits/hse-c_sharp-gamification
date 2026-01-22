# app/models/__init__.py
"""
Ensure all model modules are imported so SQLAlchemy sees every mapped class.
"""
from app.models import user  # noqa: F401
from app.models import level  # noqa: F401
from app.models import material  # noqa: F401
from app.models import test_  # noqa: F401
from app.models import question  # noqa: F401
from app.models import choice  # noqa: F401
from app.models import answer  # noqa: F401
from app.models import analytics  # noqa: F401
