# ollama-guard

Secure FastAPI proxy for Ollama (API-key and JWT auth, container-ready)

ollama-guard is a lightweight FastAPI proxy that sits in front of an Ollama server and enforces authentication and simple access controls. It accepts either a static X-API-Key or HS256 JWTs, validates optional audience/issuer claims, and forwards requests to a configured upstream Ollama instance while streaming responses back to clients. Built for easy self-hosting, containerization, and CI-driven publishing.

## Why use ollama-guard

- Add an authentication and access-control layer in front of Ollama without changing client code.
- Centralize access control with API keys or JWTs.
- Easily deployable via Docker and GitHub Actions to GitHub Container Registry (GHCR).

## Key features

- Supports X-API-Key and Bearer JWT (HS256) authentication.
- Optional JWT audience (`PROXY_JWT_AUD`) and issuer (`PROXY_JWT_ISS`) checks.
- Streams upstream responses to clients (low memory overhead).
- Preserves query params and most headers while removing sensitive ones.
- Dockerfile and GitHub Actions workflow included for CI/CD and image publication.

## Quick start (local, PowerShell)

Build the image locally:

```powershell
docker build -t ollama-guard:local .
```

Run with a static API key (example):

```powershell
docker run --rm -e PROXY_API_KEY=yourkey -e OLLAMA_UPSTREAM=https://ollama.example.com -p 8000:8000 ollama-guard:local
```

Test an endpoint:

```powershell
curl -X GET "http://127.0.0.1:8000/api/v1/ollama/models" -H "X-API-Key: yourkey"
```

## Environment variables

- `OLLAMA_UPSTREAM` — upstream Ollama base URL (no trailing slash recommended)
- `PROXY_API_KEY` — static API key to allow requests
- `PROXY_JWT_SECRET` — secret used to verify HS256 JWTs
- `PROXY_JWT_AUD` — optional JWT audience to validate
- `PROXY_JWT_ISS` — optional JWT issuer to validate

## CI / container publishing

A GitHub Actions workflow is included that builds multi-platform images and pushes them to GitHub Container Registry (GHCR). The workflow uses the repository `GITHUB_TOKEN` to authenticate by default. Change the workflow if you prefer Docker Hub or another registry.

## Next steps / suggestions

- Add an explicit healthcheck endpoint for easier orchestration.
- Add example scripts to generate test JWTs for local testing.
- Tighten the Docker image (non-root user, multi-stage build) if you need smaller or more secure images.

## License

Choose a license and add a `LICENSE` file if you plan to publish this project publicly.
