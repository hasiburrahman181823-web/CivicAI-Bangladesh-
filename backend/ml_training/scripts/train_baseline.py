"""Train on a real, user-supplied CSV. Never generate complaint records."""
import argparse
import csv
import json
from pathlib import Path
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import make_pipeline
from sklearn.metrics import classification_report

parser=argparse.ArgumentParser()
parser.add_argument('--csv',required=True)
parser.add_argument('--output',default='backend/ml_training/artifacts/baseline')
args=parser.parse_args()
with open(args.csv,encoding='utf-8-sig',newline='') as file:
    rows=list(csv.DictReader(file))
required={'text','category','original_id','incident_id','source_type'}
if not rows or not required.issubset(rows[0]):
    raise SystemExit('CSV requires text, category, original_id, incident_id, source_type columns')
if any(not r['text'].strip() or not r['original_id'].strip() or not r['incident_id'].strip() or r['source_type'] not in {'natural','derived'} for r in rows):
    raise SystemExit('Empty groups/text or invalid source_type. Annotation is required before training.')
# Union both identity relations so original versions and related incident reports cannot cross splits.
parents={}
def root(key):
    parents.setdefault(key,key)
    while parents[key]!=key:
        parents[key]=parents[parents[key]]
        key=parents[key]
    return key
for row in rows:
    a,b=root('o:'+row['original_id']),root('i:'+row['incident_id'])
    parents[a]=b
groups=[root('o:'+r['original_id']) for r in rows]
train,test=next(GroupShuffleSplit(n_splits=1,test_size=.2,random_state=42).split(rows,groups=groups))
assert not {groups[i] for i in train}&{groups[i] for i in test}
if len({rows[i]['category'] for i in train})<2:
    raise SystemExit('Training split needs at least two categories. Collect more independent incidents.')
model=make_pipeline(TfidfVectorizer(analyzer='char',ngram_range=(3,5),min_df=1,max_features=40000),LogisticRegression(max_iter=1500,class_weight='balanced'))
model.fit([rows[i]['text'] for i in train],[rows[i]['category'] for i in train])
out=Path(args.output)
out.mkdir(parents=True,exist_ok=True)
joblib.dump(model,out/'category.joblib')
reports={}
for source in ['natural','derived']:
    subset=[i for i in test if rows[i]['source_type']==source]
    reports[source]=classification_report([rows[i]['category'] for i in subset],model.predict([rows[i]['text'] for i in subset]),output_dict=True,zero_division=0) if subset else {'status':'No held-out examples of this source type'}
(out/'metrics.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding='utf-8')
(out/'split_manifest.json').write_text(json.dumps({'train_original_ids':sorted({rows[i]['original_id'] for i in train}),'test_original_ids':sorted({rows[i]['original_id'] for i in test})},indent=2),encoding='utf-8')
print('Saved model, metrics and group split manifest to',out)
