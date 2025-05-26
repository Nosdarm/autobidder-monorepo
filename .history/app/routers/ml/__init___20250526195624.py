from .ml_predictions_api import router as predictions_router
# Optionally, import other routers from the 'ml' submodule if they exist.

# This __all__ list defines what is exported when 'from app.routers.ml import *' is used.
__all__ = [
    "predictions_router",
]
