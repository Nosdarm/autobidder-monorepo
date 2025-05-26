import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base

from app.routers.auth.auth_routes                import router as auth_router
from app.routers.user.user_api                    import router as user_router
from app.routers.profiles.profiles_routes         import router as profiles_router
from app.routers.settings.profile_settings_routes import router as profile_settings_router
from app.routers.user.user_roles_routes           import router as user_roles_router
from app.routers.profiles.agency_routes           import router as agency_profiles_router
from app.routers.bids.bids_routes                 import router as bids_router
# from app.routers.ml.ml_routes                     import router as ml_router # Commented out old ML router
from app.routers.ml import predictions_router # Import the new predictions_router from app.routers.ml package
from app.routers.ml.ml_predictions_api import load_model_on_startup, internal_router as ml_internal_router # Import the startup event and internal_router
from app.routers.templates.shared_templates_routes import router as shared_templates_router
from app.routers.autobidder.autobidder_routes     import router as autobidder_router
from app.scheduler_setup import start_scheduler, shutdown_scheduler # Import scheduler functions
from app.routers.autobidder.logs                  import router as autobid_logs_router
from app.routers.ai.prompts                       import router as ai_prompts_router

app = FastAPI(debug=True)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Создаём таблицы при старте (асинхронный Engine поддерживает async with)
@app.on_event("startup")
async def on_startup_db(): # Renamed to avoid conflict if multiple on_startup named functions
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Add model loading to startup events
app.add_event_handler("startup", load_model_on_startup)
# Add scheduler startup and shutdown events
app.add_event_handler("startup", start_scheduler)
app.add_event_handler("shutdown", shutdown_scheduler)

# Подключаем роутеры
app.include_router(auth_router,             prefix="/auth",            tags=["Auth"])
app.include_router(user_router,             prefix="/users",           tags=["Users"])
app.include_router(profiles_router,         prefix="/profiles",        tags=["Profiles"])
app.include_router(profile_settings_router, prefix="/profile-settings", tags=["Profile Settings"])
app.include_router(user_roles_router,       prefix="/roles",           tags=["User Roles"])
app.include_router(agency_profiles_router,  prefix="/agency-profiles", tags=["Agency Profiles"])
app.include_router(bids_router,             prefix="/bids",            tags=["Bids"])
# app.include_router(ml_router,               prefix="/ml",              tags=["ML / Recommendations"]) # Commented out old
app.include_router(predictions_router,      prefix="/ml",              tags=["Machine Learning Predictions"]) # Added new ML router
app.include_router(ml_internal_router,      prefix="",                 tags=["Machine Learning Internal Utilities"]) # Added new ML internal router, prefix is already in the router itself
app.include_router(shared_templates_router, prefix="/templates",       tags=["Shared Templates"])
app.include_router(autobidder_router,       prefix="/autobidder",      tags=["Autobidder"])
app.include_router(autobid_logs_router,     prefix="/autobidder/logs", tags=["Autobidder Logs"])
app.include_router(ai_prompts_router,       prefix="/ai",              tags=["AI Prompts"])

# Лог всех маршрутов
def _log_routes():
    routes = "\n".join(route.path for route in app.routes)
    logging.warning("🛣️ Registered routes:\n" + routes)

_log_routes()
