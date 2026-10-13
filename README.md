# CCTV AI Remote Monitoring Platform V0.2

Runnable MVP built around an existing DW Spectrum / MVS installation.

## Flow

IP Camera -> DW Spectrum (main stream)
IP Camera -> AI Engine (sub stream) -> YOLO/Tracking -> Intrusion/Loitering -> Cloud API -> PostgreSQL/Redis -> Alarm -> Notification/DW Generic Event -> Web Portal

## Start

```bash
docker compose up --build
```

Open:
- API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- Web: http://localhost:3000

The AI engine is intended for a site GPU host. Configure `ai-engine/.env` and run:

```bash
pip install -r requirements.txt
python -m app.main
```

## V0.2 features

- Camera CRUD and zone CRUD
- YOLO person/car tracking
- Polygon intrusion detection
- Loitering timer
- Cloud event ingestion
- PostgreSQL events/alarms
- Redis alarm cooldown
- Event JPEG snapshots
- Alarm acknowledge/resolve
- DW Spectrum Generic Event adapter
- Simple customer dashboard
- PEP 8-oriented Python source

## Production work still needed

Authentication/RBAC, encrypted credentials, TLS, Alembic migrations, S3-compatible storage, email/SMS providers, retry queue, monitoring, audit log, stronger API validation, and testing against the exact DW Spectrum version.


## V0.2.1: Database initialization and camera configuration

### Database initialization

The Cloud API startup imports SQLAlchemy models and runs `Base.metadata.create_all()`.
This creates the MVP tables when the API starts. You can also run the command explicitly:

```bash
docker compose exec cloud-api python -m app.db.init_db
```

This is suitable for a prototype. Use Alembic migrations for production schema changes.

### Import the YAML camera configuration

Edit `config/cameras.example.yaml`, then import it into PostgreSQL:

```bash
curl -X POST http://localhost:8000/api/v1/admin/import-camera-config
```

The API responds with counts for cameras/zones added or updated. Import is repeatable:
existing cameras are matched by `site_id + name`, and zones by `camera_id + name`.

The Compose file mounts `./config` read-only into `/app/config`.

### How the AI Engine reads configuration

Choose one mode:

- `AI_CONFIG_MODE=cloud` (default): reads cameras and zones from Cloud API.
- `AI_CONFIG_MODE=yaml`: reads the YAML directly from `AI_CONFIG_PATH`.

For local direct-YAML testing, from the `ai-engine` directory:

```bash
AI_CONFIG_MODE=yaml
AI_CONFIG_PATH=../config/cameras.example.yaml
python -m app.main
```

Replace example RTSP URLs and credentials before connecting actual cameras.
Do not commit real camera credentials into source control.
