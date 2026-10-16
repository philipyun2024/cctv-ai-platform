from ultralytics import YOLO

model = YOLO("yolo11n.pt")

# Save the exact output path returned by the exporter
exported_path = model.export(format="openvino")

print(f"\n SUCCESS! Your OpenVINO model folder is located at:\n{exported_path}\n")