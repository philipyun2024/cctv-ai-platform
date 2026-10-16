import os
from ultralytics import YOLO

# 1. Path to your exported OpenVINO model directory
# (Ultralytics creates a folder named after your original model + _openvino_model)
model_path = "yolo11n_openvino_model"

if not os.path.exists(model_path):
    print(f"❌ Could not find OpenVINO model folder at: {model_path}")
    print("Please make sure your export step completed successfully.")
else:
    # 2. Load the optimized OpenVINO model
    print("🔄 Loading OpenVINO model...")
    model = YOLO(model_path)

    # 3. Run inference on a sample image (or a sample URL)
    print("🚀 Running benchmark inference...")
    results = model("https://ultralytics.com", device="cpu")

    # 4. Print results to console
    for result in results:
        print(f"✅ Success! Detected {len(result.boxes)} objects in the image.")
