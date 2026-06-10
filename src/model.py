import json
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.pipeline import Pipeline

from utils import create_preprocess_pipeline


def train_model(train_x: pd.DataFrame, train_y: pd.Series, rfc_params: dict):
    model = RandomForestClassifier(**rfc_params)
    pipeline = Pipeline([
        ('preprocess', create_preprocess_pipeline()),
        ('model', model)
    ])
    pipeline.fit(train_x, train_y)
    return pipeline


def evaluate_model(model: Pipeline, X_test: pd.DataFrame, y_test: pd.Series,
                   float_precision :int =4):
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    metrics = {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
    }

    metrics = json.loads(
        json.dumps(metrics), parse_float=lambda x: round(float(x), float_precision)
    )

    return metrics, y_pred, y_proba