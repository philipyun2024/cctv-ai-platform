"""Quick smoke test for the exported YOLO26n OpenVINO model.

Usage from the ai-engine directory:
    python test_openvino.py path\to\test-image.jpg
If no image is supplied, a public Ultralytics sample image is used.
"""
import sys
from pathlib import Path

from ultralytics import YOLO

MODEL_PATH = Path("yolo26n_openvino_model")
SOURCE = sys.argv[1] if len(sys.argv) > 1 else "https://ultralytics.com/images/bus.jpg"

if not MODEL_PATH.exists():
    raise SystemExit(
        f"Model folder not found: {MODEL_PATH}. Run `python export.py` first."
    )

print(f"Loading OpenVINO model: {MODEL_PATH}")
model = YOLO(str(MODEL_PATH))
print(f"Running inference on: {SOURCE}")
results = model.predict(source=SOURCE, imgsz=416, device="intel:cpu", verbose=False)
for result in results:
    print(f"Inference successful. Detections: {len(result.boxes)}")
