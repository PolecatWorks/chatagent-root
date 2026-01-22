import asyncio
import uvicorn
from pydantic import Field
from pydantic import BaseModel
from fastapi import FastAPI
from .config import HamsConfig


class HamsApp:
    def __init__(self, config: HamsConfig):
        self.config = config

        mgmt_app = FastAPI(title="Management API")

        @mgmt_app.get("/hams/alive")
        async def alive():
            return {"status": "ok"}

        @mgmt_app.get("/hams/ready")
        async def ready():
            return {"status": "ok"}

        @mgmt_app.get("/hams/shutdown")
        async def shutdown():
            return {"status": "ok"}

        @mgmt_app.get("/hams/metrics")
        async def metrics():
            return "# metrics go here"

        self.app = mgmt_app


    async def start(self):
        self.app_config= uvicorn.Config(self.app, host="0.0.0.0", port=9000, log_level="info")
        self.server = uvicorn.Server(self.app_config)

        self.task = asyncio.create_task(self.server.serve())


    async def stop(self):
        self.server.should_exit = True
        await self.task
