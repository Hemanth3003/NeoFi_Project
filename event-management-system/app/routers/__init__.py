from .auth import router as auth_router
from .events import router as events_router
from .collaboration import router as collaboration_router
from .versions import router as versions_router

__all__ = ["auth_router", "events_router", "collaboration_router", "versions_router"]