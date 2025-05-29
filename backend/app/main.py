import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request # Add Request for slowapi
from slowapi import Limiter, _rate_limit_exceeded_handler # Add slowapi imports
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.database import engine, Base
from app.config import settings # Import settings
from app.limiter import limiter # Import limiter

from app.routers.auth.auth_routes                import router as auth_router
from app.routers.user.user_api                    import router as user_router
from app.routers.profiles.profiles_routes         import router as profiles_router
from app.routers.settings.profile_settings_routes import router as profile_settings_router
from app.routers.user.user_roles_routes           import router as user_roles_router
from app.routers.profiles.agency_routes           import router as agency_profiles_router
from app.routers.bids.bids_routes                 import router as bids_router
from app.routers.ml.ml_routes                     import router as ml_router
from app.routers.templates.shared_templates_routes import router as shared_templates_router
from app.routers.autobidder.autobidder_routes     import router as autobidder_router
from app.routers.autobidder.logs                  import router as autobid_logs_router
from app.routers.ai.prompts                       import router as ai_prompts_router
from app.routers.jobs_routes                      import router as jobs_router # Added jobs_router
from app.routers import websockets as ws_router # Import WebSocket router
from app.routers.agency_routes                import router as agency_management_router # Import new agency management router

app = FastAPI(debug=settings.APP_DEBUG) # Use settings

# Initialize Limiter for rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS, # Use settings
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.services.ml_service import load_model_on_startup # Added ML model loading

from app.scheduler.scheduler import start_scheduler, shutdown_scheduler # Added scheduler imports

# Создаём таблицы при старте (асинхронный Engine поддерживает async with)
@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    load_model_on_startup() # Load ML model
    start_scheduler() # Start scheduler

@app.on_event("shutdown")
async def on_shutdown():
    shutdown_scheduler() # Shutdown scheduler

# Подключаем роутеры
app.include_router(auth_router,             prefix="/auth",            tags=["Auth"])
app.include_router(user_router,             prefix="/users",           tags=["Users"])
app.include_router(profiles_router,         prefix="/profiles",        tags=["Profiles"])
app.include_router(profile_settings_router, prefix="/profile-settings", tags=["Profile Settings"])
app.include_router(user_roles_router,       prefix="/roles",           tags=["User Roles"])
app.include_router(agency_profiles_router,  prefix="/agency-profiles", tags=["Agency Profiles"])
app.include_router(bids_router,             prefix="/bids",            tags=["Bids"])
app.include_router(ml_router,               prefix="/ml",              tags=["ML / Recommendations"])
app.include_router(shared_templates_router, prefix="/templates",       tags=["Shared Templates"])
app.include_router(autobidder_router,       prefix="/autobidder",      tags=["Autobidder"])
app.include_router(autobid_logs_router,     prefix="/autobidder/logs", tags=["Autobidder Logs"])
app.include_router(ai_prompts_router,       prefix="/ai",              tags=["AI Prompts"])
app.include_router(jobs_router,             prefix="/jobs",            tags=["Jobs"]) # Added jobs_router
app.include_router(ws_router.router,        prefix="/ws",              tags=["WebSockets"]) # Include WebSocket router
app.include_router(agency_management_router, prefix="/agency",         tags=["Agency Management"]) # Include new router

# Лог всех маршрутов
def _log_routes():
    routes = "\n".join(route.path for route in app.routes)
    logging.warning("🛣️ Registered routes:\n" + routes)

_log_routes()
