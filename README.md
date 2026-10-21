# ShiftSwap Board

A small API for posting and claiming shift swaps between two campus jobs (ASU Gammage and Sun Devil Athletics), built to learn CI/CD with GitHub Actions and Docker.

## Rules the API enforces
- A shift's end time must be after its start time
- You cannot post two overlapping shifts
- You cannot claim your own shift, a shift that is already claimed, or a shift that overlaps one you already picked up

## Endpoints
- `GET /health`
- `GET /version` returns the git commit the image was built from
- `POST /shifts`
- `GET /shifts?venue=gammage&open_only=true`
- `POST /shifts/{id}/claim`

## Run locally
```
pip install -r requirements-dev.txt
pytest
uvicorn app.main:app --reload
```

## Run with Docker
```
docker compose up --build
```
or pull the image the pipeline publishes:
```
docker run -p 8000:8000 ghcr.io/akallam04/shiftswap:latest
```

## Pipeline
Every push and pull request to `main` runs:
1. **lint**: ruff check and format check
2. **test**: pytest on Python 3.11, 3.12 and 3.13 in parallel, test reports saved as artifacts
3. **docker**: multi-stage build with layer caching, starts the container and smoke tests `/health`, `/version` and `POST /shifts`

On pushes to `main` only, the image is pushed to GitHub Container Registry tagged `latest` and the commit SHA.
