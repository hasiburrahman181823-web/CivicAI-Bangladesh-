"""Measure cross-language retrieval on derived or independently reviewed pairs."""
import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from datetime import datetime
from types import SimpleNamespace
from backend.app.services.analysis import candidate_context

import numpy as np
from sklearn.metrics import average_precision_score, f1_score, precision_score, recall_score, roc_auc_score

from backend.app.ml.embeddings import MiniLM
from backend.app.ml.text_features import normalize, romanize
from backend.ml_training.scripts.train_text import read_data
from sklearn.model_selection import StratifiedGroupKFold

def derived_rows(workbook, english):
    data = read_data(workbook)
    groups = [normalize(x[1]) for x in data]
    index = list(StratifiedGroupKFold(n_splits=5,shuffle=True,random_state=42).split(data,[x[2] for x in data],groups))
    translations = {}
    if english:
        with english.open(encoding="utf-8",newline="") as f:
            translations = {int(x["row_id"]):x["english"] for x in csv.DictReader(f) if x["english"].strip()}
    rng = np.random.default_rng(43)
    for split, indices in (("validation",index[0][1]),("test",index[1][1])):
        by_cat = defaultdict(list)
        for i in indices:
            by_cat[data[i][2]].append(int(i))
        for i in rng.permutation(indices)[:250]:
            original = data[i][1]
            pool = [j for j in by_cat[data[i][2]] if groups[j] != groups[i]]
            for lang, variant in (("Banglish",romanize), ("English",lambda s:translations.get(s[0],""))):
                others = [j for j in pool if lang == "Banglish" or data[j][0] in translations]
                if not others:
                    continue
                j = int(rng.choice(others))
                positive, negative = ((variant(original),variant(data[j][1])) if lang=="Banglish"
                                      else (variant(data[i]),variant(data[j])))
                if positive and negative:
                    yield {"split":split,"language_a":"Bangla","language_b":lang,"source_type":"derived",
                           "text_a":original,"text_b":positive,"label":1}
                    yield {"split":split,"language_a":"Bangla","language_b":lang,"source_type":"derived",
                           "text_a":original,"text_b":negative,"label":0}

def reviewed_pairs(path):
    group_splits = {}
    with path.open(encoding="utf-8-sig",newline="") as f:
        for row in csv.DictReader(f):
            if row["source_type"] not in {"natural","derived"} or row["split"] not in {"validation","test"}:
                raise ValueError("Each pair needs an explicit source_type and validation/test split")
            if row["label"] == "insufficient":
                continue
            if row["label"] not in {"0","1"} or not row["review_ref"].strip():
                raise ValueError("Provide adjudicated labels and review references")
            for key, prefix in [("original_a","original"),("original_b","original"),("incident_a","incident"),("incident_b","incident")]:
                value = row[key].strip()
                if not value:
                    raise ValueError(f"Missing verified {key}")
                if group_splits.setdefault((prefix,value),row["split"]) != row["split"]:
                    raise ValueError("An original or incident appears on both sides of the split")
            if (row["incident_a"] == row["incident_b"]) != (row["label"] == "1"):
                raise ValueError("Label contradicts reviewed incident IDs")
            yield {**row,"label":int(row["label"])}

def context_pair(row):
    endpoints = []
    for suffix in ("a","b"):
        timestamp = row.get(f"occurred_at_{suffix}","").strip()
        area = row.get(f"area_{suffix}","").strip()
        if not timestamp or not area:
            return None
        occurred = datetime.fromisoformat(timestamp)
        if occurred.tzinfo is None:
            raise ValueError("Verified timestamps must include a timezone")
        lat, lon = (row.get(f"{field}_{suffix}","").strip() for field in ("lat","lon"))
        if bool(lat) != bool(lon):
            raise ValueError("Provide both coordinates or leave both blank")
        if lat and not (-90 <= float(lat) <= 90 and -180 <= float(lon) <= 180):
            raise ValueError("Coordinates out of range")
        endpoints.append(SimpleNamespace(occurred_at=occurred,area=area,
                         latitude=float(lat) if lat else None,longitude=float(lon) if lon else None))
    return candidate_context(*endpoints) is not None

def metrics(scores, truth, threshold):
    pred = scores >= threshold
    return {"count":len(truth),"precision":float(precision_score(truth,pred,zero_division=0)),
            "recall":float(recall_score(truth,pred,zero_division=0)),"f1":float(f1_score(truth,pred,zero_division=0)),
            "average_precision":float(average_precision_score(truth,scores)),
            "roc_auc":float(roc_auc_score(truth,scores)),
            "false_merge_rate_on_negatives":float(pred[truth==0].mean())}

def run(args):
    rows = list(reviewed_pairs(args.pairs) if args.pairs else derived_rows(args.workbook,args.english))
    if not rows:
        raise ValueError("No labeled pairs available")
    encoder = MiniLM(args.model)
    text = list(dict.fromkeys(row[k] for row in rows for k in ("text_a","text_b")))
    encoded = dict(zip(text,encoder.encode(text),strict=True))
    cohorts=defaultdict(list)
    for row in rows:
        left,right=row["text_a"],row["text_b"]
        a,b=set(normalize(left).split()),set(normalize(right).split())
        cohorts[(row["source_type"],row["language_a"],row["language_b"])].append(
            (row["split"],row["label"],float(encoded[left]@encoded[right]),len(a&b)/max(1,len(a|b)),
             context_pair(row) if args.pairs else None))
    report={"evaluation":"Independent reviewed incident labels" if args.pairs else
            "Derived parallel texts and same-category negatives. Proxy for text matching only; distinct source rows may share an incident.",
            "model":"sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 quantized ONNX","cohorts":{}}
    for cohort, values in cohorts.items():
        cal=np.asarray([x[1:4] for x in values if x[0]=="validation"])
        test=np.asarray([x[1:4] for x in values if x[0]=="test"])
        if len(cal)==0 or len(test)==0 or len(set(cal[:,0]))!=2 or len(set(test[:,0]))!=2:
            raise ValueError(f"{cohort} requires both labels in validation and test")
        result={}
        for col, name in ((1,"minilm"),(2,"lexical_jaccard")):
            threshold=max(np.linspace(.05,.95,37),key=lambda t: f1_score(cal[:,0],cal[:,col]>=t,zero_division=0))
            result[name]={"validation_threshold":float(threshold),"test":metrics(test[:,col],test[:,0],threshold)}
        result["minilm_deployed_text_threshold"] = {"threshold":.65,"test":metrics(test[:,1],test[:,0],.65)}
        if args.pairs:
            known=[x for x in values if x[0]=="test" and x[4] is not None]
            if known and {x[1] for x in known} == {0,1}:
                labels=np.asarray([x[1] for x in known])
                scores=np.asarray([x[2] if x[4] else -1 for x in known])
                result["minilm_with_verified_context"]={"threshold":.65,"test":metrics(scores,labels,.65),
                                                        "eligible_test_pairs":len(known),"all_test_pairs":len(test)}
        report["cohorts"][" / ".join(cohort)] = result
    args.output.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    sources=parser.add_mutually_exclusive_group(required=True)
    sources.add_argument("--workbook",type=Path)
    sources.add_argument("--pairs",type=Path)
    parser.add_argument("--english",type=Path)
    parser.add_argument("--model",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    run(parser.parse_args())
