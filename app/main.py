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
from app.routers.ml.ml_routes                     import router as ml_router
from app.routers.templates.shared_templates_routes import router as shared_templates_router
from app.routers.autobidder.autobidder_routes     import router as autobidder_router
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
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

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

# Лог всех маршрутов
def _log_routes():
    routes = "\n".join(route.path for route in app.routes)
    logging.warning("🛣️ Registered routes:\n" + routes)

_log_routes()
