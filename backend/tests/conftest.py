import sys, os, pytest

# чтобы pytest видел пакет app
sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
)

from app.database import engine, Base, AsyncSessionLocal

# 1) Один раз в начале модуля — сброс и создание схемы
@pytest.fixture(scope="module", autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

# 2) Переопределяем get_db только для выдачи сессии
@pytest.fixture(autouse=True)
def override_get_db(monkeypatch):
    async def _get_test_db():
        async with AsyncSessionLocal() as session:
            yield session

    monkeypatch.setattr("app.database.get_db", _get_test_db)
