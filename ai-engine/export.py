"""Export YOLO26n to OpenVINO for Intel CPU inference.

Run from the ai-engine directory:
    python export.py
"""
from ultralytics import YOLO

MODEL = "yolo26n.pt"
IMAGE_SIZE = 416


def main() -> None:
    print(f"Loading {MODEL}; first run may download the weights...")
    model = YOLO(MODEL)
    exported_path = model.export(
        format="openvino",
        imgsz=IMAGE_SIZE,
        dynamic=False,
    )
    print(f"\nOpenVINO model exported to: {exported_path}")
    print("Set MODEL_PATH=yolo26n_openvino_model in ai-engine/.env")


if __name__ == "__main__":
    main()
