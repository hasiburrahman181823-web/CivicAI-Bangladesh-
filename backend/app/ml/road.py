from functools import lru_cache

import numpy as np
from PIL import Image, ImageOps

from .predict import ARTIFACTS

CLASSES = ("longitudinal_crack", "transverse_crack", "alligator_crack", "pothole")
SIZE = 640

@lru_cache(maxsize=1)
def model():
    import onnxruntime as ort
    ort.disable_telemetry_events()
    options = ort.SessionOptions()
    options.intra_op_num_threads = 2
    return ort.InferenceSession(str(ARTIFACTS/"road/road.onnx"),options,providers=["CPUExecutionProvider"])

def iou(box, others):
    start = np.maximum(box[:2],others[:,:2])
    end = np.minimum(box[2:],others[:,2:])
    intersect = np.maximum(0,end-start).prod(axis=1)
    area1 = np.maximum(0,box[2:]-box[:2]).prod()
    area2 = np.maximum(0,others[:,2:]-others[:,:2]).prod(axis=1)
    return intersect / np.maximum(1e-9,area1+area2-intersect)

def detect_road_damage(source, threshold=.3):
    image = ImageOps.exif_transpose(source).convert("RGB")
    width,height = image.size
    scale = min(SIZE/width,SIZE/height)
    size = (max(1,round(width*scale)),max(1,round(height*scale)))
    pad_x,pad_y = (SIZE-size[0])//2,(SIZE-size[1])//2
    letterbox = Image.new("RGB",(SIZE,SIZE),(114,114,114))
    letterbox.paste(image.resize(size,Image.Resampling.BILINEAR),(pad_x,pad_y))
    array = np.asarray(letterbox,dtype=np.float32).transpose(2,0,1)[None]/255
    output = model().run(None,{"image":np.ascontiguousarray(array)})[0][0].T
    classes = output[:,4:].argmax(axis=1)
    scores = output[:,4:].max(axis=1)
    order = np.argsort(-scores)
    order = order[scores[order]>=threshold][:300]
    center = output[:,:2]
    span = output[:,2:4]/2
    boxes = np.hstack((center-span,center+span))
    detections = []
    while order.size and len(detections)<30:
        best, rest = order[0],order[1:]
        x1,y1,x2,y2 = boxes[best]
        coords = [(x1-pad_x)*width/size[0],(y1-pad_y)*height/size[1],
                  (x2-pad_x)*width/size[0],(y2-pad_y)*height/size[1]]
        coords = [round(float(np.clip(value,0,limit)),1) for value,limit in zip(coords,(width,height,width,height))]
        if coords[2]>coords[0] and coords[3]>coords[1]:
            detections.append({"label":CLASSES[classes[best]],"score":round(float(scores[best]),4),"box":coords})
        order = rest[(classes[rest]!=classes[best]) | (iou(boxes[best],boxes[rest])<.45)]
    return {"model":"YOLOv8n RDD2022","width":width,"height":height,"detections":detections,
            "review_required":True,"scope":"Road surface cracks and potholes only"}
