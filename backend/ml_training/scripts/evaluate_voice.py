"""Compute corpus-level WER for audio with independently supplied transcripts."""
import argparse
import csv
import json
import re
from pathlib import Path

from backend.app.ml.text_features import normalize
from backend.app.routers.media import transcribe

def words(text):
    return re.sub(r"[^\w\u0980-\u09ff\s]"," ",normalize(text)).replace("।"," ").split()

def distance(left,right):
    prev=list(range(len(right)+1))
    for i,a in enumerate(left,1):
        current=[i]
        for j,b in enumerate(right,1):
            current.append(min(prev[j]+1,current[j-1]+1,prev[j-1]+(a!=b)))
        prev=current
    return prev[-1]

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    results={}
    with args.manifest.open(encoding="utf-8",newline="") as file:
        for row in csv.DictReader(file):
            language=row["language"]
            ref=words(row["reference"])
            audio=(args.manifest.parent/row["path"]).read_bytes()
            hyp=words(transcribe(audio,language)["text"])
            item=results.setdefault(language,{"samples":0,"reference_words":0,"edit_distance":0})
            item["samples"]+=1
            item["reference_words"]+=len(ref)
            item["edit_distance"]+=distance(ref,hyp)
    if not results or any(not row["reference_words"] for row in results.values()):
        raise ValueError("At least one nonempty reference transcript per language is required")
    for item in results.values():
        item["word_error_rate"]=item["edit_distance"]/item["reference_words"]
    args.output.write_text(json.dumps(results,indent=2)+"\n")
    print(json.dumps(results,indent=2))
