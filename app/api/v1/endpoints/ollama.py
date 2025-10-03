import os
from typing import Dict

import httpx
import jwt
from jwt import PyJWTError
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, Request
from starlette.responses import StreamingResponse

from app.ratelimit import limiter

load_dotenv()

# Upstream Ollama server and auth configuration
UPSTREAM = os.getenv("OLLAMA_UPSTREAM", "https://ollama.012140.xyz")
PROXY_API_KEY = os.getenv("PROXY_API_KEY")
PROXY_JWT_SECRET = os.getenv("PROXY_JWT_SECRET")
PROXY_JWT_AUD = os.getenv("PROXY_JWT_AUD")
PROXY_JWT_ISS = os.getenv("PROXY_JWT_ISS")

router = APIRouter()


async def verify_api_key(request: Request):
    """Allow either a static X-API-Key or a Bearer JWT.

    JWT verification uses HS256 and the secret from PROXY_JWT_SECRET.
    If PROXY_JWT_AUD/PROXY_JWT_ISS are set, they will be validated.
    """
    # 1) static API key via X-API-Key header
    api_key = request.headers.get("x-api-key")
    if PROXY_API_KEY and api_key and api_key == PROXY_API_KEY:
        return

    # 2) JWT via Authorization: Bearer <token>
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        token = auth[7:].strip()
        if not PROXY_JWT_SECRET:
            raise HTTPException(status_code=500, detail="PROXY_JWT_SECRET not configured on server")

        try:
            # Build decode kwargs
            decode_kwargs = {"algorithms": ["HS256"]}
            if PROXY_JWT_AUD:
                decode_kwargs["audience"] = PROXY_JWT_AUD
            # PyJWT's decode validates issuer only if provided in options via leeway or via verify_iss param in later versions; we'll manually check iss after decode

            payload = jwt.decode(token, PROXY_JWT_SECRET, **decode_kwargs)

            if PROXY_JWT_ISS and payload.get("iss") != PROXY_JWT_ISS:
                raise HTTPException(status_code=401, detail="Invalid token issuer")

            # Token valid
            return
        except PyJWTError:
            raise HTTPException(status_code=401, detail="Invalid token")

    # No valid auth provided
    raise HTTPException(status_code=401, detail="Unauthorized")


def _filter_response_headers(headers: Dict[str, str]) -> Dict[str, str]:
    # Remove hop-by-hop and sensitive headers
    excluded = {"transfer-encoding", "connection", "keep-alive", "proxy-authenticate", "proxy-authorization", "te", "trailers", "upgrade"}
    return {k: v for k, v in headers.items() if k.lower() not in excluded}


@router.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])  # type: ignore[arg-type]
@limiter.limit("100/minute")
async def proxy(request: Request, _=Depends(verify_api_key)):
    """Proxy any path under this router to the configured UPSTREAM.

    Example: POST /api/models -> forwards to {UPSTREAM}/models
    This preserves query params and most headers but strips Authorization/Host.
    """
    # The router is mounted at /api, so strip that prefix to get the upstream path
    # For /api/models -> models, /api/v1/tags -> v1/tags
    router_prefix = "/api"
    if not request.url.path.startswith(router_prefix + "/"):
        raise HTTPException(status_code=500, detail="Unexpected routing configuration")
    full_path = request.url.path[len(router_prefix) :].lstrip("/")
    upstream_url = f"{UPSTREAM.rstrip('/')}/{full_path}"

    method = request.method
    params = dict(request.query_params)
    incoming_headers = dict(request.headers)
    # Avoid leaking incoming auth and host
    incoming_headers.pop("authorization", None)
    incoming_headers.pop("host", None)

    body = await request.body()

    async with httpx.AsyncClient(verify=True, timeout=60.0) as client:
        resp = await client.request(method, upstream_url, params=params, headers=incoming_headers, content=body)

        filtered_headers = _filter_response_headers(resp.headers)
        media_type = resp.headers.get("content-type")

        return StreamingResponse(resp.aiter_bytes(), status_code=resp.status_code, headers=filtered_headers, media_type=media_type)
