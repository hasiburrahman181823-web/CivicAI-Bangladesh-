"""Run fixed-threshold detections on paired labeled RDD2022 images."""
import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image

from backend.app.ml.road import CLASSES, detect_road_damage, iou

if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    tp=fp=fn=count=0
    names=[]
    for path in sorted(args.directory.glob("*.jpg")):
        labels=path.with_suffix(".txt")
        if not labels.is_file():
            continue
        with Image.open(path) as im:
            result=detect_road_damage(im)
        count+=1
        names.append(path.name)
        width,height=result["width"],result["height"]
        truth=[]
        for line in labels.read_text().splitlines():
            category,x,y,w,h=map(float,line.split())
            truth.append((CLASSES[int(category)],[(x-w/2)*width,(y-h/2)*height,(x+w/2)*width,(y+h/2)*height]))
        matched=set()
        for det in result["detections"]:
            choices=[i for i,(label,_) in enumerate(truth) if label==det["label"] and i not in matched]
            if choices:
                overlap=iou(np.array(det["box"]),np.array([truth[i][1] for i in choices]))
                if max(overlap)>=.5:
                    matched.add(choices[int(overlap.argmax())])
                    tp+=1
                    continue
            fp+=1
        fn+=len(truth)-len(matched)
    if not count:
        raise ValueError("No labeled images found")
    report={"source":"https://huggingface.co/datasets/dronefreak/RDD2022","images":count,"image_ids":names,
            "scope":"Small sampled subset from checkpoint publisher test split; not independent Bangladesh validation",
            "score_threshold":.3,"iou_threshold":.5,"tp":tp,"fp":fp,"fn":fn,
            "precision":tp/max(1,tp+fp),"recall":tp/max(1,tp+fn)}
    args.output.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
