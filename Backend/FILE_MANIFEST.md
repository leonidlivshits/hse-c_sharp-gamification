PROJECT FILE MANIFEST (auto-generated) - minimal skeleton

Top-level:
- .env.example                     (example env)
- README.md                        (this file)
- requirements.txt                 (python deps)
- docker/                          (Dockerfile)
  - app.Dockerfile
- docker-compose.yml

App package (app/):
- app/main.py                      (FastAPI factory + startup/shutdown)
- app/__init__.py
- app/core/config.py               (pydantic settings)
- app/db/session.py                (async engine & session)
- app/models/__init__.py
- app/models/user.py               (sample model)
- app/schemas/user.py              (pydantic DTOs)
- app/repositories/user_repo.py
- app/services/user_service.py
- app/api/deps.py
- app/api/v1/routers/users.py
- app/api/v1/routers/materials.py
- app/api/v1/routers/tests.py
- app/health/endpoints.py
- app/cache/redis_client.py
- app/tasks/worker.py
- app/utils/

Migrations & scripts:
- alembic.ini
- migrations/env.py
- scripts/run_migrations.sh
- start.sh

Tests:
- tests/unit/test_smoke.py
- tests/integration/test_api.py

Notes:
- Many files are placeholders and contain "TODO" comments where extension is needed.
- For production, change Dockerfile, add Alembic config, remove create_all usage and rely on migrations.
