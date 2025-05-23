# backend/tests/test_prompts.py

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_crud_and_preview():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:

        # CREATE
        r = await ac.post("/ai/prompts/", json={"id":"test","prompt_text":"Echo this:"})
        assert r.status_code == 201

        # READ ALL
        r = await ac.get("/ai/prompts/")
        assert r.status_code == 200
        assert any(p["id"]=="test" for p in r.json())

        # READ ONE
        r = await ac.get("/ai/prompts/test")
        assert r.status_code == 200

        # UPDATE
        r = await ac.put("/ai/prompts/test", json={"id":"test","prompt_text":"Changed"})
        assert r.status_code == 200

        # PREVIEW 404
        r = await ac.post("/ai/prompts/preview",
                          json={"prompt_id":"nope","description":"X"})
        assert r.status_code == 404

        # PREVIEW SUCCESS
        r = await ac.post("/ai/prompts/preview",
                          json={"prompt_id":"test","description":"Hello"})
        assert r.status_code == 200
        assert "preview" in r.json()

        # DELETE
        r = await ac.delete("/ai/prompts/test")
        assert r.status_code == 204

        # CONFIRM DELETE
        r = await ac.get("/ai/prompts/test")
        assert r.status_code == 404
