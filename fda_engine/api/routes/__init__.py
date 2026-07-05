from fda_engine.api.routes.workspace import router as workspace_router
from fda_engine.api.routes.document import router as document_router
from fda_engine.api.routes.verify import router as verify_router
from fda_engine.api.routes.ws import router as ws_router

__all__ = [
    "workspace_router",
    "document_router",
    "verify_router",
    "ws_router",
]
