"""Export publisher's safetensors YOLOv8n weights to a fixed CPU ONNX graph."""
import argparse
from pathlib import Path

import torch
from safetensors.torch import load_file
from ultralytics.nn.tasks import DetectionModel

class Export(torch.nn.Module):
    def __init__(self, detector):
        super().__init__()
        self.detector = detector

    def forward(self, tensor):
        return self.detector(tensor)[0]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--weights", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    torch.set_num_threads(2)
    detector = DetectionModel("yolov8n.yaml", nc=4, verbose=False)
    detector.load_state_dict(load_file(args.weights), strict=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with torch.inference_mode():
        torch.onnx.export(Export(detector.eval()), (torch.zeros(1,3,640,640),), str(args.output),
                          input_names=["image"],output_names=["detections"],opset_version=17,dynamo=False)
