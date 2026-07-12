from __future__ import annotations

import asyncio
from uuid import uuid4

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from tests.fake_agent_target.scenarios import SCENARIOS, scenario_response
from tests.fake_agent_target.state import FakeTargetState


class ScenarioRequest(BaseModel):
    name: str
    failures: int = Field(default=0, ge=0, le=20)
    delay_seconds: float = Field(default=0.05, ge=0, le=30)


class InvokeRequest(BaseModel):
    input: str = Field(min_length=1, max_length=10_000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=10_000)


def create_fake_target_app(state: FakeTargetState | None = None) -> FastAPI:
    target_state = state or FakeTargetState()
    app = FastAPI(title="AgentTest Fake Agent Target")

    @app.post("/control/scenario")
    async def configure(request: ScenarioRequest) -> dict[str, object]:
        if request.name not in SCENARIOS:
            return JSONResponse(status_code=422, content={"error": {"code": "unknown_scenario"}})
        await target_state.configure(
            request.name, failures=request.failures, delay_seconds=request.delay_seconds
        )
        return {"scenario": request.name, "configured": True}

    @app.get("/control/observations")
    async def observations() -> dict[str, object]:
        return await target_state.snapshot()

    @app.post("/api/agent/invoke")
    async def invoke(request: InvokeRequest):
        request_id = str(uuid4())
        attempt, scenario, transient_failure = await target_state.observe(request_id, request.input)
        if scenario == "timeout":
            await asyncio.sleep(target_state.delay_seconds)
        result = scenario_response(
            scenario=scenario,
            request_id=request_id,
            attempt=attempt,
            input_text=request.input,
            transient_failure=transient_failure,
        )
        if scenario == "stream_success":

            async def stream():
                yield '{"delta":"Echo: "}\n'
                yield f'{{"delta":"{request.input}","done":true}}\n'

            return StreamingResponse(stream(), media_type="application/x-ndjson")
        return JSONResponse(status_code=result.status_code, content=result.payload)

    @app.get("/chat", response_class=HTMLResponse)
    async def chat_page() -> str:
        return (
            "<!doctype html><html><head><title>Fake Agent Target</title></head>"
            '<body><main><h1>Fake Agent Target</h1><label>Message<input id="message"></label>'
            '<button id="send">Send</button><section id="messages" aria-live="polite">'
            "</section></main></body></html>"
        )

    @app.post("/chat/messages")
    async def chat_message(request: ChatRequest) -> dict[str, object]:
        turn, history = await target_state.append_chat(request.message)
        return {"turn": turn, "history": history, "output": f"Echo: {request.message}"}

    return app


app = create_fake_target_app()
