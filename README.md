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
