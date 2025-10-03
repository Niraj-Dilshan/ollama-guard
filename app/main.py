from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.v1.endpoints import hello, ollama, health
from app.ratelimit import limiter
from app.logging_config import setup_logging
from app.middleware import log_requests


def create_app() -> FastAPI:
    setup_logging()
    app = FastAPI(title="Ollama-FastApi", version="0.1.0")
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    app.middleware("http")(log_requests)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(hello.router, prefix="/api/v1")
    app.include_router(ollama.router, prefix="/api")
    app.include_router(health.router, prefix="/api/v1")

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
