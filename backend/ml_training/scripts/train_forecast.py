"""Fit and evaluate closure-time quantiles with a chronological split."""
import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_pinball_loss
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder

MAPPING = {"Water System":"Water", "Street Condition":"Road",
           "Missed Collection":"Waste", "Dirty Condition":"Waste",
           "Street Light Condition":"Electricity", "Food Establishment":"Food",
           "Food Poisoning":"Food", "HEAT/HOT WATER":"Water"}
SOURCE = "https://data.cityofnewyork.us/d/erm2-nwe9"

def train(file, output, cutoff):
    data = pd.read_csv(file, usecols=["unique_key", "created_date", "closed_date", "complaint_type"])
    data = data.drop_duplicates("unique_key")
    created = pd.to_datetime(data.created_date, format="mixed", errors="coerce")
    closed = pd.to_datetime(data.closed_date, format="mixed", errors="coerce")
    category = data.complaint_type.map(MAPPING)
    hours = (closed-created).dt.total_seconds()/3600
    frame = pd.DataFrame({"created":created, "closed":closed, "category":category,
                          "hour":created.dt.hour, "weekday":created.dt.weekday, "hours":hours})
    frame = frame[frame.hours.ge(0) & frame.closed.le(pd.Timestamp(cutoff))].dropna().sort_values("created")
    counts = frame.category.value_counts()
    frame = frame[frame.category.isin(counts[counts >= 25].index)]
    if len(frame) < 200:
        raise ValueError("Need at least 200 historical closed requests in supported categories")
    split = frame.created.iloc[int(.8 * len(frame))]
    train_df, test = frame[(frame.created < split) & (frame.closed < split)], frame[frame.created >= split]
    test = test[test.category.isin(train_df.category)]
    if len(train_df) < 100 or len(test) < 30:
        raise ValueError("Need at least 100 pre-cutoff training outcomes and 30 later test records")
    features = ["category", "hour", "weekday"]
    models = []
    for q in (.1,.5,.9):
        pre = ColumnTransformer([("category", OneHotEncoder(handle_unknown="ignore", sparse_output=False), ["category"])], remainder="passthrough")
        model = make_pipeline(pre, GradientBoostingRegressor(loss="quantile", alpha=q, n_estimators=90, max_depth=2, min_samples_leaf=20, random_state=42))
        model.fit(train_df[features], train_df.hours)
        models.append(model)
    predictions = np.maximum(0, np.array([m.predict(test[features]) for m in models]))
    lower, middle, upper = np.sort(predictions, axis=0)
    by_category = train_df.groupby("category").hours.median()
    report = {"source":SOURCE, "target":"Creation to closure hours among supported observed closed requests",
              "scope":"NYC benchmark only; closure-only selection and local reporting differences limit transfer",
              "created_split":str(split),"observed_until":cutoff,"train":len(train_df),"test":len(test),
              "test_category_counts":test.category.value_counts().to_dict(),
              "median_model_mae_hours":float(mean_absolute_error(test.hours,middle)),
              "category_median_baseline_mae_hours":float(mean_absolute_error(test.hours,test.category.map(by_category))),
              "interval_empirical_coverage":float(((test.hours>=lower)&(test.hours<=upper)).mean()),
              "quantile_pinball_hours":{str(q):float(mean_pinball_loss(test.hours,row,alpha=q)) for q,row in zip((.1,.5,.9),predictions)}}
    output.mkdir(parents=True, exist_ok=True)
    joblib.dump({"models":models,"categories":sorted(train_df.category.unique())},output/"forecast.joblib",compress=3)
    (output/"forecast_metrics.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))

if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--observed-until",required=True)
    args=parser.parse_args()
    train(args.csv,args.output,args.observed_until)
