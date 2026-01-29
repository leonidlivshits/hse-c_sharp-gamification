# HSE Gamification Backend - skeleton

This directory contains a minimal FastAPI async backend skeleton (Postgres + Redis).

How to run:
1. Copy environment:
   cp .env.example .env
2. Start services:
   docker compose up --build

The app under development is at: http://localhost:8000
Health: http://localhost:8000/health/live
Docs (OpenAPI): http://localhost:8000/docs

Files and TODOs are marked at the top of each file.
