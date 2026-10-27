"""앱 실행 및 설정.

실행:  cd backend && python main.py      (http://127.0.0.1:8000 에서 화면까지 함께 열림)
또는:  cd backend && uvicorn main:app --reload
"""
from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))  # 어느 폴더에서 실행해도 import 되도록

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Mount
from starlette.staticfiles import StaticFiles

from config import Settings, get_settings
from repositories.db import connect, init_db
from repositories.persona_repository import PersonaRepository
from repositories.place_repository import PlaceRepository
from routers import chat, places, rooms, weather
from services.chat_service import ChatService, ClientFactory
from services.place_service import PlaceService
from services.prompt_service import PromptService
from services.room_service import RoomService
from services.weather_service import ForecastFetcher, WeatherService


def build_services(settings: Settings, client_factory: ClientFactory | None = None,
                   weather_fetcher: ForecastFetcher | None = None) -> SimpleNamespace:
    conn = connect(settings.db_path)
    init_db(conn, settings.data_dir)
    persona_repo = PersonaRepository(conn)
    place_svc = PlaceService(PlaceRepository(conn))
    room_svc = RoomService(persona_repo)
    weather_svc = WeatherService(settings.weather_timeout, weather_fetcher)
    prompt_svc = PromptService(settings.knowledge_dir)
    chat_svc = ChatService(settings, room_svc, persona_repo, prompt_svc, place_svc, weather_svc, client_factory)
    return SimpleNamespace(settings=settings, conn=conn, rooms=room_svc, places=place_svc,
                           weather=weather_svc, prompts=prompt_svc, chat=chat_svc)


def create_app(settings: Settings | None = None, client_factory: ClientFactory | None = None,
               weather_fetcher: ForecastFetcher | None = None) -> Starlette:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: Starlette):
        app.state.services = build_services(settings, client_factory, weather_fetcher)
        yield
        app.state.services.conn.close()

    api = [*chat.routes, *rooms.routes, *places.routes, *weather.routes]
    routes = [Mount("/api", routes=api)]
    if settings.frontend_dir.exists():  # 화면(frontend/)도 같은 주소에서 제공
        routes.append(Mount("/", StaticFiles(directory=str(settings.frontend_dir), html=True), name="frontend"))

    middleware = []
    if settings.cors_origins:  # 화면을 다른 주소에서 띄울 때만 필요
        middleware.append(Middleware(CORSMiddleware, allow_origins=list(settings.cors_origins),
                                     allow_methods=["GET", "POST"], allow_headers=["Content-Type"]))
    return Starlette(routes=routes, middleware=middleware, lifespan=lifespan)


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)
