# CCTV AI Remote Monitoring Platform V0.3.0 — YOLO26 Windows AI Engine

Runnable MVP built around an existing DW Spectrum / MVS installation.

## Flow

IP Camera -> DW Spectrum (main stream)
IP Camera -> AI Engine (sub stream) -> YOLO26n/OpenVINO + ByteTrack -> Intrusion/Loitering -> Cloud API -> PostgreSQL/Redis -> Alarm -> Notification/DW Generic Event -> Web Portal

## Start

```bash
docker compose up --build
```

Open:
- API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- Web: http://localhost:3000

The AI Engine runs directly on Windows, outside Docker. It reads cameras/zones from Cloud API by default, pulls each RTSP substream, and sends detected events back to Cloud API. Import the camera configuration after startup and replace sample RTSP URLs/credentials before connecting real cameras.

```powershell
# In the project root, start only the Docker services:
docker compose ps

# In a separate PowerShell window, run the AI Engine locally:
cd ai-engine
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
# Export the lightweight YOLO26n model to Intel OpenVINO format (first run downloads weights)
python export.py
$env:AI_CONFIG_MODE = "cloud"
$env:CLOUD_API_URL = "http://localhost:8000"
$env:MODEL_PATH = "yolo26n_openvino_model"
$env:IMAGE_SIZE = "416"
$env:DEVICE = "cpu"
$env:TRACKER = "bytetrack.yaml"
$env:DETECTION_CLASSES = "0,2"
python -m app.main
```

If PowerShell blocks virtual-environment activation, use Command Prompt and run `.venv\Scripts\activate.bat` instead. Ensure Python dependencies and a compatible PyTorch/Ultralytics setup are installed on the Windows machine.

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


## Debug / troubleshooting (V0.2.2)

### Enable detailed logs

Set these variables in the `.env` file used by Docker Compose:

```dotenv
LOG_LEVEL=DEBUG
DEBUG_LOGGING=true
```

Restart services after changing environment variables:

```bash
docker compose up -d --build
docker compose logs -f --tail=200 cloud-api
```

The AI engine is a separate Python process and should be started with the same logging variables in its environment. To follow its logs, use the terminal where it is running, or its container logs if you have added it as a Compose service.

### Diagnostic endpoints

- `GET /health`: confirms the Cloud API process responds.
- `GET /health/db`: performs a real `SELECT 1` database check; HTTP 503 means inspect Cloud API logs and database connectivity.
- `GET /docs`: interactive API docs.

### Useful commands

```bash
docker compose ps
docker compose logs --tail=200 postgres
docker compose logs --tail=200 redis
docker compose logs --tail=300 cloud-api
curl http://localhost:8000/health
curl http://localhost:8000/health/db
curl http://localhost:8000/api/v1/cameras
```

### Log contents

Cloud API logs request method/path/status/duration, database startup and health-check failures, camera/config import operations, event ingestion, alarm creation and cooldown suppression. AI engine logs config source, camera stream connection/reconnects, frame dimensions, YOLO model loading, detection counts at DEBUG level, event submissions, and DW Spectrum API failures. RTSP URLs and camera credentials are intentionally not printed.

**Note:** `DEBUG` mode can generate many log lines and may include API response error text. Use it for short troubleshooting windows, then return to `INFO`. Never paste logs containing public IPs, usernames, camera IDs, or customer details into public forums without reviewing them.


## V0.3.0 — YOLO26n on Windows / Intel CPU

The AI Engine remains a native Windows Python process. It is **not** a Docker Compose service. Docker continues to run PostgreSQL, Redis, Cloud API, and the Web Dashboard only.

### Recommended setup for Intel Core i3-14100

1. Install 64-bit Python 3.11 or 3.12 and create the `ai-engine/.venv` virtual environment.
2. From `ai-engine`, install dependencies with `python -m pip install -r requirements.txt`.
3. Run `python export.py` once to download `yolo26n.pt` and export `yolo26n_openvino_model` at 416-pixel input size.
4. Keep the local `ai-engine/.env` file and change `MODEL_PATH=yolo26n_openvino_model`; set `IMAGE_SIZE=416`, `DEVICE=cpu`, `TRACKER=bytetrack.yaml`, `DETECTION_CLASSES=0,2`, and `AI_TARGET_FPS=2.0`.
5. Start the engine with `python -m app.main`.

`DETECTION_CLASSES=0,2` detects COCO person and car classes. Use `DETECTION_CLASSES=0` for person-only intrusion detection. ByteTrack maintains object IDs across sampled frames; the existing polygon zone rules still decide whether an intrusion or loitering event occurs. `AI_TARGET_FPS` caps the YOLO sampling rate per camera (default 2 FPS); it is a target cap, not a guaranteed processing rate. The AI Engine logs measured per-camera detection FPS and average inference time about once per minute.

For CPU troubleshooting, first use one camera and a substream (for example 640x360 or 704x480), then check DEBUG logs. OpenVINO may improve CPU inference speed; actual FPS depends on stream resolution, camera count, and scene complexity. The code uses `asyncio.to_thread()` for stream reads and inference so one blocking read/inference is less likely to stall other async camera workers.

### Model test

From the `ai-engine` directory: `python test_openvino.py path\to\test-image.jpg`. If no path is provided, the script uses a public sample image and requires internet access.

### Secret handling

Do not commit `.env` files or real RTSP credentials. The source archive intentionally excludes local `.env` files and replaces sample camera URLs with placeholders. Preserve your own local `.env` separately and update only the model settings above.


## V0.3.1 — Per-camera AI sampling rate

Configure the Windows AI Engine in `ai-engine/.env`:

```dotenv
AI_TARGET_FPS=2.0
AI_POLL_INTERVAL=0.0
```

The engine continues reading each RTSP stream but skips frames until that camera's next sampling interval. `AI_TARGET_FPS=2` means at most one YOLO inference every 0.5 seconds per camera when the engine can keep up. If inference is slower, actual FPS will be lower. The engine reports measured detection FPS and average inference time per camera approximately every 60 seconds. For four cameras, 2 FPS per camera corresponds to a target total of 8 inference frames per second.
